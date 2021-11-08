set(VCPKG_TARGET_ARCHITECTURE x64)
# We link to the dynamic CRT (build with /MD) even when making static libs
set(VCPKG_CRT_LINKAGE dynamic)
set(VCPKG_LIBRARY_LINKAGE static)

# HACK for physx...
set(VCPKG_POLICY_SKIP_DUMPBIN_CHECKS enabled)
