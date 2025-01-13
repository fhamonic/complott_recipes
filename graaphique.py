from colorama import Fore, Back, Style
import jsonschema
import docker
import json
import os
import sys

root_path = os.path.dirname(__file__)
recipes_path = os.path.join(root_path, "recipes")
downloaded_ressources_path = os.path.join(root_path, "ressources", "downloaded")
generated_ressources_path = os.path.join(root_path, "ressources", "generated")
pages_path = os.path.join(root_path, "pages")
verbose = False

print(Fore.GREEN + "Building Docker image..." + Style.RESET_ALL)
client = docker.from_env()
try:
    image, logs = client.images.build(
        path=os.path.join(root_path, "docker_config"),
        tag="recipe-sandbox",
        buildargs={"UID": str(os.getuid()), "GID": str(os.getgid())},
    )
    if verbose:
        print(logs)
except docker.errors.BuildError as e:
    if e.build_log:
        for log_entry in e.build_log:
            if "stream" in log_entry:
                print(log_entry["stream"], end="")
            elif "errorDetail" in log_entry:
                print(Fore.RED + log_entry["errorDetail"]["message"] + Style.RESET_ALL)
    sys.exit(os.EX_CONFIG)


print(Fore.GREEN + "Reading recipes..." + Style.RESET_ALL)
recipe_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "generate_ressources": {"type": "boolean"},
        "pages": {"type": "object"},
        "required_ressources": {
            "type": "object",
            "properties": {
                "downloaded": {"type": "object"},
                "generated": {"type": "array", "items": "string"},
            },
        },
    },
}
recipes = {}
for item in os.listdir(recipes_path):
    if not os.path.isdir(os.path.join(recipes_path, item)):
        print(
            Fore.YELLOW
            + f"Warning: File '{item}' should not be in the 'recipes' folder."
            + Style.RESET_ALL
        )
        continue
    recipe_name = item
    recipe_path = os.path.join(recipes_path, recipe_name)

    recipe_json_path = os.path.join(recipe_path, "recipe.json")
    if not os.path.exists(recipe_json_path):
        print(
            Fore.YELLOW
            + f"Skipped recipe '{recipe_name}': 'recipe.json' not found."
            + Style.RESET_ALL
        )
        continue
    with open(recipe_json_path) as f:
        d = json.load(f)
        try:
            jsonschema.validate(d, recipe_schema)
        except jsonschema.ValidationError as e:
            print(
                Fore.YELLOW
                + f"Skipped recipe '{recipe_name}': 'recipe.json' has invalid scheme:\n"
                + e.schema.get("error_msg", e.message)
                + Style.RESET_ALL
            )
            continue
        recipes[recipe_name] = d

print(Fore.GREEN + "Downloading ressources..." + Style.RESET_ALL)
# TODO

print(Fore.GREEN + "Running recipes..." + Style.RESET_ALL)
# TODO

# recipe_name = "pcs"
# volumes = {}
# volumes[os.path.join(recipes_path, recipe_name)] = {
#     "bind": "/app/recipe",
#     "mode": "ro",
# }
# volumes[downloaded_ressources_path] = {
#     "bind": "/app/ressources/downloaded",
#     "mode": "ro",
# }
# volumes[os.path.join(generated_ressources_path, "pcs")] = {
#     "bind": "/app/ressources/generated/pcs",
#     "mode": "rw",
# }

# print(Fore.GREEN + f"Running recipe '{recipe_name}'..." + Style.RESET_ALL)

# try:
#     container_logs = client.containers.run(
#         "recipe-sandbox", remove=True, read_only=True, volumes=volumes
#     )
#     if verbose:
#         print(container_logs.decode("utf-8"))
# except docker.errors.ContainerError as e:
#     print(Fore.RED + e.stderr.decode("utf-8") + Style.RESET_ALL)
#     sys.exit(os.EX_SOFTWARE)
