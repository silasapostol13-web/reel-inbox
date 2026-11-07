#!/usr/bin/env python3
"""Builds the 'Send to Claude' iOS Shortcut and signs it so it can be opened on the iPhone.

Flow on the phone: Share sheet (or copied link, when run on its own) -> Send to Claude -> type or dictate a note -> saved as
iCloud Drive/Shortcuts/ReelInbox/reel-<time>.json -> 'Sent to Claude' notification.

    python3 shortcut/build_shortcut.py   # writes shortcut/Send to Claude.shortcut (signed)
"""
import plistlib
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
OBJ = "￼"  # placeholder char Shortcuts uses where a variable sits inside text


def out(uid, name, aggr=None):
    a = {"Type": "ActionOutput", "OutputUUID": uid, "OutputName": name}
    if aggr:
        a["Aggrandizements"] = aggr
    return a


def attachment(value):
    return {"Value": value, "WFSerializationType": "WFTextTokenAttachment"}


def text(*parts):
    """Text made of plain strings and variables (dicts)."""
    s, ranges = "", {}
    for p in parts:
        if isinstance(p, str):
            s += p
        else:
            ranges[f"{{{len(s)}, 1}}"] = p
            s += OBJ
    return {"Value": {"string": s, "attachmentsByRange": ranges}, "WFSerializationType": "WFTextTokenString"}


def action(ident, params):
    return {"WFWorkflowActionIdentifier": ident, "WFWorkflowActionParameters": params}


u_urls, u_note, u_date, u_dict = (str(uuid.uuid4()).upper() for _ in range(4))
u_if = str(uuid.uuid4()).upper()
iso = [{"Type": "WFDateFormatVariableAggrandizement", "WFDateFormatStyle": "ISO 8601", "WFISO8601IncludeTime": True}]
stamp = [{"Type": "WFDateFormatVariableAggrandizement", "WFDateFormatStyle": "Custom",
          "WFDateFormat": "yyyyMMdd-HHmmss"}]

actions = [
    action("is.workflow.actions.detect.link", {
        "UUID": u_urls,
        "WFInput": attachment({"Type": "ExtensionInput"}),
    }),
    # No link (e.g. run from the Action Button with something else copied): say so on the phone and stop.
    action("is.workflow.actions.conditional", {
        "GroupingIdentifier": u_if, "WFControlFlowMode": 0, "WFCondition": 101,
        "WFInput": {"Type": "Variable", "Variable": attachment(out(u_urls, "URLs"))},
    }),
    action("is.workflow.actions.alert", {
        "WFAlertActionTitle": "No link found",
        "WFAlertActionMessage": "Share a Reel to Send to Claude, or copy the Reel's link first and run it again.",
        "WFAlertActionCancelButtonShown": False,
    }),
    action("is.workflow.actions.exit", {}),
    action("is.workflow.actions.conditional", {"GroupingIdentifier": u_if, "WFControlFlowMode": 2}),
    action("is.workflow.actions.ask", {
        "UUID": u_note,
        "WFAskActionPrompt": "Why are you sending this, and for which project?",
        "WFInputType": "Text",
        "WFAllowsMultilineText": True,
    }),
    action("is.workflow.actions.date", {"UUID": u_date, "WFDateActionMode": "Current Date"}),
    action("is.workflow.actions.dictionary", {
        "UUID": u_dict,
        "WFItems": {"Value": {"WFDictionaryFieldValueItems": [
            {"WFItemType": 0, "WFKey": text("url"), "WFValue": text(out(u_urls, "URLs"))},
            {"WFItemType": 0, "WFKey": text("note"), "WFValue": text(out(u_note, "Provided Input"))},
            {"WFItemType": 0, "WFKey": text("sent_at"), "WFValue": text(out(u_date, "Date", iso))},
            {"WFItemType": 0, "WFKey": text("source"), "WFValue": text("Send to Claude shortcut v1")},
        ]}, "WFSerializationType": "WFDictionaryFieldValue"},
    }),
    action("is.workflow.actions.documentpicker.save", {
        "WFInput": attachment(out(u_dict, "Dictionary")),
        "WFAskWhereToSave": False,
        "WFSaveFileOverwrite": False,
        "WFFileDestinationPath": text("/ReelInbox/reel-", out(u_date, "Date", stamp), ".json"),
    }),
    action("is.workflow.actions.notification", {
        "WFNotificationActionTitle": "Sent to Claude",
        "WFNotificationActionBody": text("Your Mac will process it in a minute or two."),
        "WFNotificationActionSound": False,
    }),
]

shortcut = {
    "WFWorkflowActions": actions,
    "WFWorkflowClientVersion": "2607.0.2",
    "WFWorkflowMinimumClientVersion": 900,
    "WFWorkflowMinimumClientVersionString": "900",
    "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983, "WFWorkflowIconGlyphNumber": 59511},
    "WFWorkflowImportQuestions": [],
    "WFWorkflowTypes": ["ActionExtension"],
    "WFWorkflowInputContentItemClasses": ["WFURLContentItem", "WFStringContentItem"],
    "WFWorkflowOutputContentItemClasses": [],
    "WFWorkflowHasOutputFallback": False,
    "WFWorkflowHasShortcutInputVariables": True,
    # Run without sharing (Action Button, Back Tap, home-screen icon): use the copied link instead.
    "WFWorkflowNoInputBehavior": {"Name": "WFWorkflowNoInputBehaviorGetClipboard", "Parameters": {}},
    "WFQuickActionSurfaces": [],
}

unsigned = HERE / "Send to Claude.unsigned.shortcut"
signed = HERE / "Send to Claude.shortcut"
unsigned.write_bytes(plistlib.dumps(shortcut, fmt=plistlib.FMT_BINARY))
r = subprocess.run(["shortcuts", "sign", "--mode", "anyone", "--input", str(unsigned), "--output", str(signed)],
                   capture_output=True, text=True)
print(r.stdout, r.stderr, file=sys.stderr)
if r.returncode != 0 or not signed.exists():
    sys.exit(f"signing failed (exit {r.returncode})")
print(signed)
