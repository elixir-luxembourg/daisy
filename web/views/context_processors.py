import pkg_resources

def daisy_version(request):
    try:
        daisy_packages = pkg_resources.require("elixir-daisy")

        if len(daisy_packages) == 0:
            the_version = "develop"
        else:
            the_version = daisy_packages[0].version
    except:
        the_version = "develop"
    
    return {
        "app_version": the_version
    }
