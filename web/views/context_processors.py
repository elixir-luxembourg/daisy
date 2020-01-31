import pkg_resources

def daisy_version(request):
    daisy_packages = pkg_resources.require("elixir-daisy")

    if len(daisy_packages) == 0:
        the_version = "undefined"
    else:
        the_version = daisy_packages[0].version

    return {
        "app_version": the_version
    }
