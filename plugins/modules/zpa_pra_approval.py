#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2023 Zscaler Inc, <devrel@zscaler.com>

#                             MIT License
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: zpa_pra_approval
short_description: Create a PRA Approval Controller.
description:
  - This module will create/update/delete Privileged Remote Access Approval.
author:
  - William Guilherme (@willguibr)
version_added: "1.1.0"
requirements:
    - Zscaler SDK Python can be obtained from PyPI U(https://pypi.org/project/zscaler-sdk-python/)

extends_documentation_fragment:
  - zscaler.zpacloud.fragments.provider
  - zscaler.zpacloud.fragments.documentation
  - zscaler.zpacloud.fragments.state

options:
  id:
    type: str
    description: "The unique identifier of the privileged approval"
    required: false
  email_ids:
    description: The email address of the user that you are assigning the privileged approval to
    required: false
    type: list
    elements: str
  start_time:
    type: str
    description: "The start date that the user has access to the privileged approval i.e Tue, 07 May 2024 11:05:30 PST"
    required: false
  end_time:
    type: str
    description: The end date that the user no longer has access to the privileged approval i.e Tue, 07 Jun 2024 11:05:30 PST
    required: false
  application_ids:
    description:
      - The unique identifier of the pra application segment.
    type: list
    elements: str
    required: false
  working_hours:
    description: "Privileged Approval WorkHours configuration."
    type: dict
    required: false
    suboptions:
      days:
        description: "The days of the week when the privileged approval is active."
        type: list
        elements: str
        choices:
          - MON
          - TUE
          - WED
          - THU
          - FRI
          - SAT
          - SUN
      start_time:
        description: "The local start time for the privileged approval."
        type: str
        required: false
      start_time_cron:
        description:
            - "The cron expression for the start time of the privileged approval, specifying the exact time of day the approval begins."
            - "Example: '0 15 10 ? * MON-FRI' starts the approval at 10:15 AM on weekdays."
        type: str
        required: false
      end_time:
        description: "The local end time for the privileged approval."
        type: str
        required: false
      end_time_cron:
        description:
            - "The cron expression for the end time of the privileged approval, specifying the exact time of day the approval ends."
            - "Example: '0 0 18 ? * MON-FRI' ends the approval at 6:00 PM on weekdays."
        type: str
        required: false
      time_zone:
        description: "The IANA time zone identifier for the privileged approval's timing."
        type: str
        required: false
"""

EXAMPLES = """
- name: Create PRA Approval
  zscaler.zpacloud.zpa_pra_approval:
    provider: '{{ zpa_cloud }}'
    state: present
    email_ids:
      - 'jdoe@example.com'
    start_time: 'Thu, 09 May 2024 8:00:00 PST'
    end_time: 'Mon, 10 Jun 2024 5:00:00 PST'
    application_ids:
      - '216199618143356658'
      - '216199618143356661'
    working_hours:
      days:
        - 'FRI'
        - 'MON'
        - 'SAT'
        - 'SUN'
        - 'THU'
        - 'TUE'
        - 'WED'
      start_time: '09:00'
      end_time: '17:00'
      start_time_cron: '0 0 16 ? * MON,TUE,WED,THU,FRI,SAT,SUN'
      end_time_cron: '0 0 0 ? * MON,TUE,WED,THU,FRI,SAT,SUN'
      time_zone: 'America/Vancouver'
  register: result
"""

RETURN = """
# The newly created privileged approval resource record.
"""


from traceback import format_exc
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.zscaler.zpacloud.plugins.module_utils.zpa_client import (
    ZPAClientHelper,
)
from ansible_collections.zscaler.zpacloud.plugins.module_utils.utils import (
    deleteNone,
)


def normalize_approval(approval):
    """
    Normalize rule data by setting computed values.
    """
    normalized = approval.copy()

    computed_values = [
        "id",
        "start_time",
        "end_time",
        # "application_ids",
    ]
    for attr in computed_values:
        normalized.pop(attr, None)

    return normalized


def core(module):
    state = module.params.get("state", None)
    client = ZPAClientHelper(module)
    approval = dict()
    params = [
        "id",
        "email_ids",
        "start_time",
        "end_time",
        "application_ids",
        "working_hours",
    ]
    for param_name in params:
        approval[param_name] = module.params.get(param_name, None)
    approval_id = approval.get("id", None)
    email_ids = approval.get("email_ids", None)

    existing_approval = None
    if approval_id is not None:
        approval_box = client.privileged_remote_access.get_approval(
            approval_id=approval_id
        )
        if approval_box is not None:
            existing_approval = approval_box.to_dict()
    elif email_ids is not None:
        approvals = client.privileged_remote_access.list_approval().to_list()
        for approval_ in approvals:
            if approval_.get("email_ids") == email_ids:
                existing_approval = approval_
                break

    desired_approval = normalize_approval(approval)
    current_approval = (
        normalize_approval(existing_approval) if existing_approval else {}
    )

    fields_to_exclude = ["id"]
    differences_detected = False
    for key, value in desired_approval.items():
        if key not in fields_to_exclude and current_approval.get(key) != value:
            differences_detected = True
            module.warn(
                f"Difference detected in {key}. Current: {current_approval.get(key)}, Desired: {value}"
            )

    if existing_approval is not None:
        id = existing_approval.get("id")
        existing_approval.update(approval)
        existing_approval["id"] = id

    module.warn(f"Final payload being sent to SDK: {approval}")
    if state == "present":
        if existing_approval is not None:
            if differences_detected:
                """Update"""
                existing_approval = deleteNone(
                    {
                        "approval_id": existing_approval.get("id"),
                        "email_ids": existing_approval.get("email_ids"),
                        "start_time": existing_approval.get("start_time"),
                        "end_time": existing_approval.get("end_time"),
                        "application_ids": existing_approval.get("application_ids"),
                        "working_hours": existing_approval.get("working_hours"),
                    }
                )
                module.warn("Payload Update for SDK: {}".format(existing_approval))
                existing_approval = client.privileged_remote_access.update_approval(
                    **existing_approval
                ).to_dict()
                module.exit_json(changed=True, data=existing_approval)
            else:
                """No Changes Needed"""
                module.exit_json(changed=False, data=existing_approval)
        else:
            module.warn("Creating pra approval as no existing approval was found")
            """Create"""
            approval_cleaned = deleteNone(
                {
                    "email_ids": approval.get("email_ids"),
                    "start_time": approval.get("start_time"),
                    "end_time": approval.get("end_time"),
                    "application_ids": approval.get("application_ids"),
                    "working_hours": approval.get("working_hours"),
                }
            )
            module.warn(f"Payload for SDK: {approval_cleaned}")
            approval_response = client.privileged_remote_access.add_approval(
                **approval_cleaned
            )
            module.exit_json(changed=True, data=approval_response)
    elif (
        state == "absent"
        and existing_approval is not None
        and existing_approval.get("id") is not None
    ):
        code = client.privileged_remote_access.delete_approval(
            approval_id=existing_approval.get("id")
        )
        if code > 299:
            module.exit_json(changed=False, data=None)
        module.exit_json(changed=True, data=existing_approval)
    module.exit_json(changed=False, data={})


def main():
    argument_spec = ZPAClientHelper.zpa_argument_spec()
    argument_spec.update(
        id=dict(type="str", required=False),
        email_ids=dict(type="list", elements="str", required=False),
        start_time=dict(type="str", required=False),
        end_time=dict(type="str", required=False),
        application_ids=dict(type="list", elements="str", required=False),
        working_hours=dict(
            type="dict",
            options=dict(
                days=dict(
                    type="list",
                    elements="str",
                    required=False,
                    choices=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
                ),
                start_time=dict(type="str", required=False),
                start_time_cron=dict(type="str", required=False),
                end_time=dict(type="str", required=False),
                end_time_cron=dict(type="str", required=False),
                time_zone=dict(type="str", required=False),
            ),
            required=False,
        ),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == "__main__":
    main()
