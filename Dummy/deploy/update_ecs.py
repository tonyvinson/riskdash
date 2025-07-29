import boto3
import click


def get_current_task_definition(client, cluster, service):
    response = client.describe_services(cluster=cluster, services=[service])
    current_task_arn = response["services"][0]["taskDefinition"]

    response = client.describe_task_definition(taskDefinition=current_task_arn)
    return response


@click.command()
@click.option("--cluster", help="Name of the ECS cluster", required=True)
@click.option("--service", help="Name of the ECS service", required=True)
def deploy(cluster, service):
    client = boto3.client("ecs")

    container_definitions = []
    response = get_current_task_definition(client, cluster, service)
    print(response["taskDefinition"])
    for container_definition in response["taskDefinition"]["containerDefinitions"]:
        new_def = container_definition.copy()
        container_definitions.append(new_def)

    new_task_definition = response["taskDefinition"]
    new_task_definition["containerDefinitions"] = container_definitions
    new_task_definition.pop("taskDefinitionArn")
    new_task_definition.pop("revision")
    new_task_definition.pop("status")
    new_task_definition.pop("requiresAttributes")
    new_task_definition.pop("compatibilities")
    new_task_definition.pop("registeredAt")
    new_task_definition.pop("registeredBy")

    # response = client.register_task_definition(
    #     family=response["taskDefinition"]["family"],
    #     volumes=response["taskDefinition"]["volumes"],
    #     containerDefinitions=container_definitions,
    # )
    response = client.register_task_definition(**new_task_definition)

    new_task_arn = response["taskDefinition"]["taskDefinitionArn"]

    response = client.update_service(
        cluster=cluster,
        service=service,
        taskDefinition=new_task_arn,
    )


if __name__ == "__main__":
    deploy()
