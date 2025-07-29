doc## Initial Setup for AWS Account

1. ### Create an S3 Bucket for Terraform State

    This bucket will be used to store the Terraform State.

    Bucket Name: **fedrisk-api-tf-state-yyyy-mm-dd**

    - Create the Bucket in region **us-east-1**
    - Block all Public Access should be **checked**
    - Enable **versioning** for the bucket.

    Ensure that this name is updated in line **7** of **main.tf**
    Ensure that this name is updated in lines **18** and **27** of **iam_policy_ci_user.json**

2. ### Create a DynamoDB table to hold a state lock

    This table will be used to ensure that terraform cannot be run simultaneously from two different locations.

    Table Name: **fedrisk-api-tf-state-lock**
    Partition Key: **LockID**

    Ensure that this name is updated in line **11** of **main.tf**
    Ensure that this name is updated in line **59** of **iam_policy_ci_user.json**

3. ### Create an Elastic Container Registry ECR

    This is where all docker images will be pushed.

    Repository Name: **fedrisk-api**

    - Scan On Push should be **checked**

    Ensure that this name is updated in line **48** of **iam_policy_ci_user.json**

4. ### Create IAM Policy for the CI User

    Use the json file **iam_policy_ci_user.json** (after ensuring that any name changes have been updated in that file).

    Policy Name: **Fedrisk-Api-CI**
    Description: **Policy for our Fedrisk-Api-CI user**

5. ### Create IAM User for CI

    This is the iam user that will be used for all CI/CD work.

    Username: **fedrisk-api-ci**
    Access type: **Programmatic access**
    Permissions: select "Attach existing policies directly" and select **Fedrisk-Api-CI**

    Copy and Store the **AWS_ACCESS_KEY** and **AWS_SECRET_ACCESS_KEY** for the new user. We will need to set up variable for CI/CD later . . .

6. ### Create SSH Key Pair and Upload to AWS

   ```
   ssh-keygen -t rsa -C "fedrisk-api-bastion" -f ~/.ssh/fedrisk-api-bastion
   ```

    - **Import the key either using the AWS UI or with the aws cli**

   ```
    aws ec2 import-key-pair --key-name "fedrisk-api-bastion" --public-key-material fileb://~/.ssh/fedrisk-api-bastion.pub
   ```
