import pkg_resources

def daisy_version(request):
    try:
        daisy_packages = pkg_resources.require("elixir-daisy")

        if len(daisy_packages) == 0:
            the_version = "undefined"
        else:
            the_version = daisy_packages[0].version
    except:
        the_version = "undefined"
    finally:
        return {
            "app_version": the_version
        }
