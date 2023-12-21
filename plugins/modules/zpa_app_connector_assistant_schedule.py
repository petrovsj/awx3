#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2023, Zscaler, Inc

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import absolute_import, division, print_function

__metaclass__ = type

DOCUMENTATION = """
---
module: zpa_app_connector_assistant_schedule
short_description: Configures Auto Delete for the specified disconnected App Connector.
description:
  - This module will configure Auto Delete for the specified disconnected App Connector.
author:
  - William Guilherme (@willguibr)
version_added: "1.0.0"
requirements:
    - Zscaler SDK Python can be obtained from PyPI U(https://pypi.org/project/zscaler-sdk-python/)
extends_documentation_fragment:
    - zscaler.zpacloud.fragments.credentials_set
    - zscaler.zpacloud.fragments.provider
options:
  id:
    description:
        - The unique identifier for the App Connector auto deletion configuration for a customer.
        - This field is only required for the PUT request to update the frequency of the App Connector Settings.
    required: false
    type: str
  customer_id:
    description: The unique identifier of the ZPA tenant.
    required: false
    type: str
  enabled:
    description: Indicates if the setting for deleting App Connectors is enabled or disabled.
    required: false
    type: bool
  delete_disabled:
    description: Indicates if the App Connectors are included for deletion if they are in a disconnected state based on frequencyInterval and frequency values.
    required: false
    type: bool
  frequency:
    description: The scheduled frequency at which the disconnected App Connectors are deleted.
    required: false
    type: str
    choices: days
  frequency_interval:
    description: The interval for the configured frequency value. The minimum supported value is 5.
    required: false
    type: str
    choices: '5', '7', '14', '30', '60', '90'
"""

EXAMPLES = """
- name: Enable / Update App Connector Auto Delete
  zscaler.zpacloud.zpa_app_connector_assistant_schedule:
    provider: "{{ zpa_cloud }}"
    customer_id: '123456778901011'
    enabled: true
    delete_disabled: true
    frequency: 'days'
    frequency_interval: '5'

"""

RETURN = """
# Returns information on a specified App Connector Group.
"""

from traceback import format_exc

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
import os
from ansible_collections.zscaler.zpacloud.plugins.module_utils.zpa_client import (
    ZPAClientHelper,
)

# The def core (module) function is where all the logic for the resource should go in
def core(module):
    state = module.params.get("state", None)
    customer_id = module.params.get("customer_id")
    enabled = module.params.get("enabled")
    delete_disabled = module.params.get("delete_disabled")
    frequency = module.params.get("frequency")
    frequency_interval = module.params.get("frequency_interval")

    client = ZPAClientHelper(module)

    # Attempt to get the current schedule
    try:
        schedule = client.connectors.get_connector_schedule(customer_id=customer_id)
        scheduler_id = schedule.get('id') if schedule else None
    except Exception as e:
        module.fail_json(msg=f"Failed to get schedule: {to_native(e)}")

    # If schedule is None or empty, it means we need to create a new schedule
    if not schedule:
        if enabled:
            try:
                client.connectors.add_connector_schedule(frequency, frequency_interval, delete_disabled)
                module.exit_json(changed=True, message="Schedule added successfully.")
            except Exception as e:
                if "resource.already.exist" in str(e):
                    scheduler_id = 'some_default_or_retrieved_id'  # Retrieve the actual id here
                else:
                    module.fail_json(msg=f"Failed to add schedule: {to_native(e)}")
        else:
            module.exit_json(changed=False, message="Schedule is not enabled.")
        return

    # Get the current values from the schedule
    current_enabled = schedule.get('enabled') if schedule else None
    current_delete_disabled = schedule.get('delete_disabled') if schedule else None
    current_frequency = schedule.get('frequency') if schedule else None
    current_frequency_interval = schedule.get('frequency_interval') if schedule else None

    # Determine if an update is necessary
    differences_detected = False
    for key, current_value, desired_value in [
        ("enabled", current_enabled, enabled),
        ("delete_disabled", current_delete_disabled, delete_disabled),
        ("frequency", current_frequency, frequency),
        ("frequency_interval", current_frequency_interval, frequency_interval)
    ]:
        if current_value != desired_value:
            differences_detected = True
            module.warn(f"Difference detected in {key}. Current: {current_value}, Desired: {desired_value}")

    if differences_detected and scheduler_id:
        try:
            update_result = client.connectors.update_schedule(scheduler_id, customer_id=customer_id, enabled=enabled,
                                                              delete_disabled=delete_disabled, frequency=frequency,
                                                              frequency_interval=frequency_interval)
            if update_result:
                module.exit_json(changed=True, message="Schedule updated successfully.")
            else:
                module.fail_json(msg="Failed to update schedule: Update not successful")
        except Exception as e:
            module.fail_json(msg=f"Failed to update schedule: {to_native(e)}")
    elif not scheduler_id:
        module.fail_json(msg="Schedule ID not found for updating the schedule.")
    else:
        module.exit_json(changed=False, message="No update required.")



def main():
    # Retrieve customer_id from the environment variable if available
    env_customer_id = os.getenv('ZPA_CUSTOMER_ID')

    argument_spec = ZPAClientHelper.zpa_argument_spec()
    argument_spec.update(
        id=dict(type="str", required=False),
        customer_id=dict(type="str", required=False, default=env_customer_id),
        enabled=dict(type="bool", required=False),
        delete_disabled=dict(type="bool", required=False),
        frequency=dict(type="str", required=False, default='days'),
        frequency_interval=dict(
            type="str",
            required=False,
            default="5",
            choices=["5", "7", "14", "30", "60", "90"],
        ),
                state=dict(type="str", choices=["present"], default="present"),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    try:
        core(module)
    except Exception as e:
        module.fail_json(msg=to_native(e), exception=format_exc())


if __name__ == "__main__":
    main()
