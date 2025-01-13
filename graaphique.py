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
verbose = True

print(Fore.GREEN + "Building Docker image...." + Style.RESET_ALL)
client = docker.from_env()
try:
    image, logs = client.images.build(
        path=os.path.join(root_path, "docker_config"),
        tag="recipe-sandbox",
        buildargs={"UID": str(os.getuid()), "GID": str(os.getgid())},
    )
    if verbose:
        for line in logs:
            if "stream" in line:
                print(line["stream"], end="")
except docker.errors.BuildError as e:
    if e.build_log:
        for log_entry in e.build_log:
            if "stream" in log_entry:
                print(log_entry["stream"], end="")
            elif "errorDetail" in log_entry:
                print(Fore.RED + log_entry["errorDetail"]["message"] + Style.RESET_ALL)
    sys.exit(os.EX_CONFIG)


print(Fore.GREEN + "Reading recipes.........." + Style.RESET_ALL)
recipe_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "authors": {"type": "array", "items": {"type": "string"}},
        "tags": {"type": "array", "items": {"type": "string"}},
        "generate_ressources": {"type": "boolean"},
        "pages": {
            "type": "object",
            "patternProperties": {
                "^.*$": {
                    "type": "string",
                    "pattern": '^(?![ .])[^<>:"/\\|?*\r\n]+(?<![ .])$',
                }
            },
        },
        "required_ressources": {
            "type": "object",
            "properties": {
                "downloaded": {
                    "type": "object",
                    "patternProperties": {
                        '^(?![ .])[^<>:"/\\|?*\r\n]+(?<![ .])$': {
                            "type": "string",
                            "pattern": "^https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}(?:[-a-zA-Z0-9()@:%_\+.~#?&\/=]*)$",
                        }
                    },
                },
                "generated": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
    },
    "required": ["title", "authors", "tags"],
    "additionalProperties": False,
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
                + f"Skipped recipe '{recipe_name}' because 'recipe.json' has invalid scheme:\n"
                + e.schema.get("error_msg", e.message)
                + Style.RESET_ALL
            )
            continue
        recipes[recipe_name] = d

print(Fore.GREEN + "Verifying integrity......" + Style.RESET_ALL)

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


def normalize_url(url):
    parsed = urlparse(url)
    netloc = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.port and parsed.port not in (80, 443):
        netloc += f":{parsed.port}"
    path = parsed.path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query)))
    return urlunparse((parsed.scheme.lower(), netloc, path, parsed.params, query, ""))


invalid_recipe_names = []
ressources_to_generate_for_recipes = {}
ressources_to_download_for_recipes = {}
for recipe_name, recipe in recipes.items():
    if "required_ressources" in recipe:
        if "generated" in recipe["required_ressources"]:
            for required_recipe_name in recipe["required_ressources"]["generated"]:
                if required_recipe_name not in recipes:
                    print(
                        Fore.YELLOW
                        + f"Skipped recipe '{recipe_name}' because dependency '{required_recipe_name}' is unknown.\n"
                        + Style.RESET_ALL
                    )
                    invalid_recipe_names.append(recipe_name)
                    continue
                if not recipes["required_recipe_name"]["generate_ressources"]:
                    print(
                        Fore.YELLOW
                        + f"Skipped recipe '{recipe_name}' because dependency '{required_recipe_name}' does not generate ressources.\n"
                        + Style.RESET_ALL
                    )
                    invalid_recipe_names.append(recipe_name)
                    continue
                if required_recipe_name not in ressources_to_generate_for_recipes:
                    ressources_to_generate_for_recipes[required_recipe_name] = []
                ressources_to_generate_for_recipes[required_recipe_name].append(
                    recipe_name
                )
        if "downloaded" in recipe["required_ressources"]:
            for ressource_alias, ressource_url in recipe["required_ressources"][
                "downloaded"
            ].items():
                normalized_ressource_url = normalize_url(ressource_url)
                if normalized_ressource_url not in ressources_to_download_for_recipes:
                    ressources_to_download_for_recipes[normalized_ressource_url] = []
                ressources_to_download_for_recipes[normalized_ressource_url].append(
                    recipe_name
                )

for invalid_recipe_name in invalid_recipe_names:
    del recipes[recipe_name]

unfulfilled_recipes_requirements = {
    recipe_name: recipe["required_ressources"]
    for recipe_name, recipe in recipes.items()
}


print(Fore.GREEN + "Downloading ressources..." + Style.RESET_ALL)
for ressource_url, requiring_recipes in ressources_to_download_for_recipes.items():
    pass
# TODO

print(Fore.GREEN + "Running recipes.........." + Style.RESET_ALL)
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
