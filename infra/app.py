#!/usr/bin/env python3

import aws_cdk as cdk

from glue_stack import PersonalGlueETLStack


app = cdk.App()

PersonalGlueETLStack(
    app,
    "PersonalGlueETLStack",
    env=cdk.Environment(
        account=app.node.try_get_context("aws_account"),
        region=app.node.try_get_context("aws_region")
    )
)

app.synth()
