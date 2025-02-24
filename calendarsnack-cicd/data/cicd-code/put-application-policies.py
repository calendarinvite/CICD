"""Creates application policies to share SAM apps with OUs."""

import os

import boto3


def lambda_handler(event, context):
    """Handle lambda event."""
    print(f"Event: {event}\nContext: {context}")
    print("Getting OU Data")
    ou_data = get_ou_data()

    print("Putting application policy")
    put_application_policy(ou_data)

    return None


def get_ou_data() -> dict:
    """Return dictionary of organization unit info."""
    # Get principal account id
    # You cannot reference the principal account in an application policy
    session = boto3.Session()
    sts_client = session.client("sts")
    principal_account = sts_client.get_caller_identity().get("Account")

    # Organization Unit aliases that will be granted access to applications
    org_units = os.environ["OrgUnits"].split(",")

    org_client = session.client("organizations")

    # We need the root Organization id to find the corresponding
    # Organization Unit IDs for each alias
    root = org_client.list_roots()["Roots"][0]["Id"]

    ous = org_client.list_organizational_units_for_parent(
        ParentId=root, MaxResults=20
    )

    # Filter out only the OrgUnits that match the aliases
    ou_data = [
        {"alias": ou["Name"], "id": ou["Id"]}
        for ou in ous["OrganizationalUnits"]
        if ou["Name"] in org_units
    ]

    # Gather the accounts listed under our Org Units
    for ou in ou_data:
        alias, ou_id = ou.values()
        print(alias, ou_id)
        print(f"Compiling statement for {alias}")
        response = org_client.list_accounts_for_parent(ParentId=ou_id)
        account_ids = [
            account["Id"]
            for account in response["Accounts"]
            if not account["Id"] == principal_account
        ]
        print(f"There are {len(account_ids)} accounts for {alias}")

        # Compile the policy statement for each OrgUnit
        if len(account_ids):
            statement = {
                "Actions": ["Deploy"],
                "PrincipalOrgIDs": [],
                "Principals": account_ids,
                "StatementId": alias,
            }

            ou["Statement"] = statement

    return ou_data


def put_application_policy(ou_data: dict):
    """Put application policy for application with access to Accout IDs."""
    session = boto3.Session()
    sam_client = session.client("serverlessrepo")

    applications = sam_client.list_applications(MaxItems=100)

    while applications.get("NextToken"):
        applications["Applications"].append(
            sam_client.list_applications(
                MaxItems=100, NextToken=applications["NextToken"]
            )
        )

    app_ids = [
        app["ApplicationId"]
        for app in applications["Applications"]
        if os.environ["FilterLabel"] in app["Labels"]
    ]

    print(f"There are {len(app_ids)} applications.")

    for app_id in app_ids:
        response = sam_client.put_application_policy(
            ApplicationId=app_id,
            Statements=[
                ou.get("Statement") for ou in ou_data if ou.get("Statement")
            ],
        )
        print(response)

    return None
