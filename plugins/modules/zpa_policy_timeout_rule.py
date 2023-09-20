#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright: (c) 2022, William Guilherme <wguilherme@securitygeek.io>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = """
---
module: zpa_policy_timeout_rule
short_description: Create a Policy Timeout Rule
description:
  - This module create/update/delete a Policy Timeout Rule in the ZPA Cloud.
author:
  - William Guilherme (@willguibr)
version_added: "1.0.0"
requirements:
    - Zscaler SDK Python can be obtained from PyPI U(https://pypi.org/project/zscaler-sdk-python/)
options:
  client_id:
    description: ""
    required: false
    type: str
  client_secret:
    description: ""
    required: false
    type: str
  customer_id:
    description: ""
    required: false
    type: str
  action:
    description:
      - This is for providing the rule action.
    type: str
    required: false
    choices:
      - RE_AUTH
  priority:
    type: str
    required: false
    description: ""
  reauth_default_rule:
    type: bool
    required: false
    description: ""
  id:
    description: ""
    type: str
    required: false
  policy_type:
    description: ""
    type: str
    required: false
  rule_order:
    description: ""
    type: str
    required: false
  default_rule:
    description:
      - This is for providing a customer message for the user.
    type: bool
    required: false
  operator:
    description:
      - This denotes the operation type.
    type: str
    required: false
    choices:
      - AND
      - OR
  description:
    description:
      - This is the description of the access policy.
    type: str
    required: false
  custom_msg:
    description:
      - This is for providing a customer message for the user.
    type: str
    required: false
  name:
    type: str
    required: True
    description:
      - This is the name of the timeout policy.
  default_rule_name:
    type: str
    required: false
    description: ""
  reauth_idle_timeout:
    type: str
    required: false
    description: ""
  reauth_timeout:
    type: str
    required: false
    description: ""
  conditions:
    type: list
    elements: dict
    required: False
    description: ""
    suboptions:
      id:
        description: ""
        type: str
      negated:
        description: ""
        type: bool
        required: False
      operator:
        description: ""
        type: str
        required: True
      operands:
        description: ""
        type: list
        elements: dict
        required: False
        suboptions:
          id:
            description: ""
            type: str
          idp_id:
            description: ""
            type: str
            required: False
          name:
            description: ""
            type: str
            required: False
          lhs:
            description: ""
            type: str
            required: True
          rhs:
            description: ""
            type: str
            required: False
          object_type:
            description: ""
            type: str
            required: True
  state:
    description: "Whether the app should be present or absent."
    type: str
    choices:
      - present
      - absent
    default: present

"""

EXAMPLES = """
- name: "Policy Timeout Rule - Example"
  zscaler.zpacloud.zpa_policy_timeout_rule:
    name: "Policy Timeout Rule - Example"
    description: "Policy Timeout Rule - Example"
    action: "RE_AUTH"
    rule_order: 1
    reauth_idle_timeout: 600
    reauth_timeout: 172800
    operator: "AND"
    conditions:
      - negated: false
        operator: "OR"
        operands:
          - name: "app_segment"
            object_type: "APP"
            lhs: "id"
            rhs: "216196257331292105"
      - negated: false
        operator: "OR"
        operands:
          - name: "segment_group"
            object_type: "APP_GROUP"
            lhs: "id"
            rhs: "216196257331292103"
      - negated: false
        operator: "OR"
        operands:
          - name: "zpn_client_type_exporter"
            object_type: "CLIENT_TYPE"
            lhs: "id"
            rhs: "zpn_client_type_exporter"
          - name: "zpn_client_type_browser_isolation"
            object_type: "CLIENT_TYPE"
            lhs: "id"
            rhs: "zpn_client_type_browser_isolation"
          - name: "zpn_client_type_zapp"
            object_type: "CLIENT_TYPE"
            lhs: "id"
            rhs: "zpn_client_type_zapp"
      - negated: false
        operator: "OR"
        operands:
          - name: "CrowdStrike_ZPA_ZTA_40"
            object_type: "POSTURE"
            lhs: "13ba3d97-aefb-4acc-9e54-6cc230dee4a5"
            rhs: "true"
"""

RETURN = """
# The newly created policy access timeout rule resource record.
"""

from traceback import format_exc

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.zscaler.zpacloud.plugins.module_utils.zpa_client import (
    ZPAClientHelper,
    deleteNone,
)


def map_conditions(conditions_obj):
    result = []
    for condition in conditions_obj:
        operands = condition.get("operands")
        if operands is not None and isinstance(operands, list):
            for op in operands:
                if (
                    op.get("object_type", None) is not None
                    and op.get("lhs", None) is not None
                    and op.get("rhs", None) is not None
                ):
                    operand = (
                        op.get("object_type", None),
                        op.get("lhs", None),
                        op.get("rhs", None),
                    )
                    result.append(operand)
    return result


def core(module):
    state = module.params.get("state", None)
    client = ZPAClientHelper(module)
    policy_rule_id = module.params.get("id", None)
    policy_rule_name = module.params.get("name", None)
    policy = dict()
    params = [
        "id",
        "name",
        "description",
        "policy_type",
        "action",
        "reauth_idle_timeout",
        "reauth_timeout",
        "operator",
        "rule_order",
        "conditions",
    ]
    for param_name in params:
        policy[param_name] = module.params.get(param_name, None)
    existing_policy = None
    if policy_rule_id is not None:
        existing_policy = client.policies.get_rule(
            policy_type="timeout", rule_id=policy_rule_id
        )
    elif policy_rule_name is not None:
        rules = client.policies.list_rules(policy_type="timeout").to_list()
        for rule in rules:
            if rule.get("name") == policy_rule_name:
                existing_policy = rule
                break
    if existing_policy is not None:
        id = existing_policy.get("id")
        existing_policy.update(policy)
        existing_policy["id"] = id
    if state == "present":
        if existing_policy is not None:
            """Update"""
            existing_policy = deleteNone(
                dict(
                    policy_type="timeout",
                    rule_id=existing_policy.get("id", None),
                    name=existing_policy.get("name", None),
                    description=existing_policy.get("description", None),
                    action=existing_policy.get("action", "").upper(),
                    reauth_idle_timeout=existing_policy.get(
                        "reauth_idle_timeout", None
                    ),
                    reauth_timeout=existing_policy.get("reauth_timeout", None),
                    conditions=map_conditions(existing_policy.get("conditions", [])),
                )
            )
            existing_policy = client.policies.update_rule(**existing_policy)
            module.exit_json(changed=True, data=existing_policy)
        else:
            """Create"""
            policy = deleteNone(
                dict(
                    name=policy.get("name", None),
                    description=policy.get("description", None),
                    action=policy.get("action", None),
                    reauth_idle_timeout=policy.get("reauth_idle_timeout", None),
                    reauth_timeout=policy.get("reauth_timeout", None),
                    conditions=map_conditions(policy.get("conditions", [])),
                )
            )
            policy = client.policies.add_timeout_rule(**policy)
            module.exit_json(changed=False, data=policy)
    elif state == "absent" and existing_policy is not None:
        code = client.policies.delete_rule(
            policy_type="timeout", rule_id=existing_policy.get("id")
        )
        if code > 299:
            module.exit_json(changed=False, data=None)
        module.exit_json(changed=True, data=existing_policy)
    module.exit_json(changed=False, data={})


def main():
    argument_spec = ZPAClientHelper.zpa_argument_spec()
    argument_spec.update(
        id=dict(type="str"),
        name=dict(type="str", required=True),
        description=dict(type="str", required=False),
        policy_type=dict(type="str", required=False),
        action=dict(type="str", required=False, choices=["RE_AUTH"]),
        reauth_idle_timeout=dict(type="str", required=True),
        reauth_timeout=dict(type="str", required=True),
        operator=dict(type="str", required=False, choices=["AND", "OR"]),
        rule_order=dict(type="str", required=False),
        conditions=dict(
            type="list",
            elements="dict",
            options=dict(
                id=dict(type="str"),
                negated=dict(type="bool", required=False),
                operator=dict(type="str", required=True, choices=["AND", "OR"]),
                operands=dict(
                    type="list",
                    elements="dict",
                    options=dict(
                        id=dict(type="str"),
                        idp_id=dict(type="str", required=False),
                        name=dict(type="str", required=False),
                        lhs=dict(type="str", required=True),
                        rhs=dict(type="str", required=False),
                        object_type=dict(
                            type="str",
                            required=True,
                            choices=[
                                "APP",
                                "APP_GROUP",
                                "CLIENT_TYPE",
                                "SAML",
                                "IDP",
                                "SCIM",
                                "SCIM_GROUP",
                                "TRUSTED_NETWORK",
                                "EDGE_CONNECTOR_GROUP",
                                "POSTURE",
                            ],
                        ),
                    ),
                    required=False,
                ),
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
