## Configuration Notes

These notes refer to the terraform configuration and highlight changes that may be desired at some point.

1. On line **37** of **database.tf**, we define a **backup_retention_period** of **0**.  This
will result in **no backups** being done for the database.  This initial setting is simply to save money during development.  When ready to go to production, you will definitely want to change this value to something more like **7** (for 7 days of backup to be constantly maintained).

2. On line **38** of **database.tf**, we define a **multi_az** of **false**. This will result in a single accessibility zone being used for the database and will save money during development.  You will definitely want to change this value to **true** when you move to production.

3. On line **39** of **database.tf**, we define **skip_final_snapshot** of **true**.  This setting
will allow Terraform to easily be able to delete and re-create database.  It is recommended that we keep this setting to avoid maintenance issues due to the fact that a unique final snapshot needs to be made each time you delete a database.

4. File **sample.tfvars** contains the **layout** (set of variables that must be supplied).
    - This file is designed to be copied into a file named **terraform.tfvars** with a set of values that you actually want to use when running terraform from a user's laptop.

    **Note:** the file **terraform.tfvars** is ignored by **.gitignore** so you don't worry that
    secrets get pushed into your git repository.
