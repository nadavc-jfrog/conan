from conans.errors import (conanfile_exception_formatter, ConanInvalidConfiguration)
from conans.model.conan_file import get_env_context_manager
from conans.util.conan_v2_mode import conan_v2_behavior, CONAN_V2_MODE_ENVVAR
from conans.util.env_reader import get_env


def run_configure_method(conanfile, down_options, down_ref, ref):
    """ Run all the config-related functions for the given conanfile object """

    # Avoid extra time manipulating the sys.path for python
    with get_env_context_manager(conanfile, without_python=True):
        if hasattr(conanfile, "config"):
            conan_v2_behavior("config() has been deprecated. "
                              "Use config_options() and configure()",
                              v1_behavior=conanfile.output.warn)
            with conanfile_exception_formatter(str(conanfile), "config"):
                conanfile.config()

        with conanfile_exception_formatter(str(conanfile), "config_options"):
            conanfile.config_options()

        conanfile.options.propagate_upstream(down_options, down_ref, ref)

        if hasattr(conanfile, "config"):
            with conanfile_exception_formatter(str(conanfile), "config"):
                conanfile.config()

        with conanfile_exception_formatter(str(conanfile), "configure"):
            conanfile.configure()

        conanfile.settings.validate()  # All has to be ok!
        conanfile.options.validate()

        _validate_fpic(conanfile)


def _validate_fpic(conanfile):
    v2_mode = get_env(CONAN_V2_MODE_ENVVAR, False)
    toolchain = hasattr(conanfile, "toolchain")

    if not (toolchain or v2_mode):
        return
    fpic = conanfile.options.get_safe("fPIC")
    if fpic is None:
        return
    os_ = conanfile.settings.get_safe("os")
    if os_ and "Windows" in os_:
        if v2_mode:
            raise ConanInvalidConfiguration("fPIC option defined for Windows")
        conanfile.output.error("fPIC option defined for Windows")
        return
    shared = conanfile.options.get_safe("shared")
    if shared:
        if v2_mode:
            raise ConanInvalidConfiguration("fPIC option defined for a shared library")
        conanfile.output.error("fPIC option defined for a shared library")
