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
            + f"Warning: skipped recipe '{recipe_name}': 'recipe.json' not found."
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
                + f"Warning: skipped recipe '{recipe_name}' because 'recipe.json' has invalid scheme:\n"
                + e.schema.get("error_msg", e.message)
                + Style.RESET_ALL
            )
            continue
        if "required_ressources" not in d:
            d["required_ressources"] = {}
        if "generated" not in d["required_ressources"]:
            d["required_ressources"]["generated"] = []
        if "downloaded" not in d["required_ressources"]:
            d["required_ressources"]["downloaded"] = {}
        if "generate_ressources" not in d:
            d["generate_ressources"] = False
        recipes[recipe_name] = d

print(Fore.GREEN + "Verifying integrity......" + Style.RESET_ALL)

from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from urllib.request import urlretrieve
from hashlib import sha1


def normalize_url(url):
    parsed = urlparse(url)
    netloc = parsed.hostname.lower() if parsed.hostname else ""
    if parsed.port and parsed.port not in (80, 443):
        netloc += f":{parsed.port}"
    path = parsed.path.rstrip("/")
    query = urlencode(sorted(parse_qsl(parsed.query)))
    return urlunparse((parsed.scheme.lower(), netloc, path, parsed.params, query, ""))


def hash_string(s):
    return str(int(sha1(s.encode("utf-8")).hexdigest(), 16) % 10**16)


invalid_recipe_names = []
ressources_to_generate_for_recipes = {}
ressources_to_download_for_recipes = {}
for recipe_name, recipe in recipes.items():
    for required_recipe_name in recipe["required_ressources"]["generated"]:
        if required_recipe_name not in recipes:
            print(
                Fore.YELLOW
                + f"Warning: skipped recipe '{recipe_name}' because dependency '{required_recipe_name}' is unknown."
                + Style.RESET_ALL
            )
            invalid_recipe_names.append(recipe_name)
            continue
        if not recipes["required_recipe_name"]["generate_ressources"]:
            print(
                Fore.YELLOW
                + f"Warning: skipped recipe '{recipe_name}' because dependency '{required_recipe_name}' does not generate ressources."
                + Style.RESET_ALL
            )
            invalid_recipe_names.append(recipe_name)
            continue
        if required_recipe_name not in ressources_to_generate_for_recipes:
            ressources_to_generate_for_recipes[required_recipe_name] = []
        ressources_to_generate_for_recipes[required_recipe_name].append(recipe_name)

    for ressource_alias, ressource_url in recipe["required_ressources"][
        "downloaded"
    ].items():
        normalized_ressource_url = normalize_url(ressource_url)
        recipe["required_ressources"]["downloaded"][
            ressource_alias
        ] = normalized_ressource_url
        if normalized_ressource_url not in ressources_to_download_for_recipes:
            ressources_to_download_for_recipes[normalized_ressource_url] = []
        ressources_to_download_for_recipes[normalized_ressource_url].append(recipe_name)

for invalid_recipe_name in invalid_recipe_names:
    del recipes[recipe_name]

unfulfilled_recipes_requirements = {
    recipe_name: {
        "downloaded": list(recipe["required_ressources"]["downloaded"].values()),
        "generated": recipe["required_ressources"]["generated"],
    }
    for recipe_name, recipe in recipes.items()
}


def notify_downloaded_ressource(ressource_url):
    for requiring_recipe in ressources_to_download_for_recipes[ressource_url]:
        unfulfilled_recipes_requirements[requiring_recipe]["downloaded"].remove(
            ressource_url
        )


print(Fore.GREEN + "Downloading ressources..." + Style.RESET_ALL)
ressources_index_path = os.path.join(downloaded_ressources_path, "index.json")
if os.path.exists(ressources_index_path):
    with open(ressources_index_path, "r") as f:
        ressources_index = json.load(f)
else:
    ressources_index = {}

for ressource_url, requiring_recipes in ressources_to_download_for_recipes.items():
    if ressource_url not in ressources_index:
        ressource_file_name = hash_string(ressource_url)
        ressource_path = os.path.join(downloaded_ressources_path, ressource_file_name)
        try:
            urlretrieve(ressource_url, ressource_path)
        except Exception as e:
            print(
                Fore.YELLOW
                + f"Warning: failed to download ressource '{ressource_url}' ({e})"
                + Style.RESET_ALL
            )
            if os.path.exists(ressource_path):
                os.remove(ressource_path)
            continue
        ressources_index[ressource_url] = ressource_file_name
    notify_downloaded_ressource(ressource_url)

with open(ressources_index_path, "w") as f:
    json.dump(ressources_index, f)


print(Fore.GREEN + "Running recipes.........." + Style.RESET_ALL)
import queue

recipes_to_run = queue.Queue()


def can_recipe_be_run(recipe_name):
    unfulfilled_downloads = unfulfilled_recipes_requirements[recipe_name]["downloaded"]
    unfulfilled_generations = unfulfilled_recipes_requirements[recipe_name]["generated"]
    return len(unfulfilled_downloads) == 0 and len(unfulfilled_generations) == 0


def notify_generated_ressource(ressource_name):
    if ressource_name not in ressources_to_generate_for_recipes:
        return
    for requiring_recipe_name in ressources_to_generate_for_recipes[ressource_name]:
        unfulfilled_recipes_requirements[requiring_recipe_name]["generated"].remove(
            ressource_name
        )
        if can_recipe_be_run(required_recipe_name):
            recipes_to_run.put(recipe_name)


for recipe_name in recipes.keys():
    if can_recipe_be_run(recipe_name):
        recipes_to_run.put(recipe_name)


while not recipes_to_run.empty():
    recipe_name = recipes_to_run.get()
    recipe = recipes[recipe_name]

    volumes = {}
    volumes[os.path.join(recipes_path, recipe_name)] = {
        "bind": "/app/recipe",
        "mode": "ro",
    }
    for ressource_alias, ressource_url in recipe["required_ressources"][
        "downloaded"
    ].items():
        volumes[
            os.path.join(downloaded_ressources_path, ressources_index[ressource_url])
        ] = {
            "bind": f"/app/ressources/downloaded/{ressource_alias}",
            "mode": "ro",
        }
    for required_ressource_name in recipe["required_ressources"]["generated"]:
        volumes[os.path.join(generated_ressources_path, required_ressource_name)] = {
            "bind": f"/app/ressources/generated/{required_ressource_name}",
            "mode": "ro",
        }
    if recipe["generate_ressources"]:
        volumes[os.path.join(generated_ressources_path, recipe_name)] = {
            "bind": f"/app/ressources/generated/{recipe_name}",
            "mode": "rw",
        }
    for page_folder in recipe["pages"].values():
        volumes[os.path.join(pages_path, recipe_name, page_folder)] = {
            "bind": f"/app/pages/{recipe_name}/{page_folder}",
            "mode": "rw",
        }

    if verbose:
        print(f"Running recipe '{recipe_name}'...")

    try:
        container_logs = client.containers.run(
            "recipe-sandbox", remove=True, read_only=True, volumes=volumes
        )
        if verbose:
            print(container_logs.decode("utf-8"))
    except docker.errors.ContainerError as e:
        print(Fore.RED + e.stderr.decode("utf-8") + Style.RESET_ALL)
        sys.exit(os.EX_SOFTWARE)

    if recipe["generate_ressources"]:
        notify_generated_ressource(recipe_name)
