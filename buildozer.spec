[app]

# (str) Title of your application
title = 德语学习助手

# (str) Package name
package.name = deutsch_lernen

# (str) Package domain (needed for android/ios packaging)
package.domain = org.deutschlernen

# (str) Source code where the main.py live
source.dir = mobile

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,md,txt,ttf,otf

# (list) List of inclusions using pattern matching
source.include_patterns = resources/*,src/*,config.json,fonts/*

# (str) Application versioning (method 1)
version = 0.4.0

# (list) Application requirements
# 这里列出应用需要的Python包
requirements = python3,kivy==2.3.0,pyjnius,android,plyer,requests,openai,pillow,ffpyplayer

# (str) Supported orientation (one of landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (string) Presplash background color (for new android toolchain)
# Supported formats are: #RRGGBB #AARRGGBB
# Possible values are: any hex color value
presplash_color = #FFFFFF

# (string) Presplash animation filename
# leave empty if you don't want a presplash animation
presplash.filename = resources/icons/presplash.png

# (string) Icon filename
icon.filename = resources/icons/app_icon.png

# (list) Permissions
# 添加需要的安卓权限
android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,RECORD_AUDIO,MODIFY_AUDIO_SETTINGS

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (list) p4a whitelist
# whitelist =

# (str) Python-for-android branch to use, defaults to master
# p4a.branch = master

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) enables Android auto backup feature
# android.allow_backup = True

# (str) The format used to package the app for release (aab or apk)
# android.release_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
# p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
# p4a.local_recipes =

# (str) Filename to open the list of recipes
# p4a.recipes =

# (str) Custom recipe to use
# p4a.custom_recipe =

#
# iOS specific
#

# (str) Path to a custom kivy-ios folder
# ios.kivy_ios_dir =

# (str) Name of the certificate to use for signing the debug version
# ios.codesign.debug =

# (str) Name of the certificate to use for signing the release version
# ios.codesign.release =

#
# Android specific
#

# (bool) Copy library instead of making a libpymodules.so
# android.copy_libs = 1

# (str) The Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
# android.archs = arm64-v8a, armeabi-v7a

# (int) overrides automatic compilation of java files
# android.javaCompile = 1

# (str) The format used to package the app for release mode (aab or apk).
# android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aab).
# android.debug_artifact = apk

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin

#    -----------------------------------------------------------------------------
#    List as in https://pypi.org/simple/
#    Extra indexes used
#    -----------------------------------------------------------------------------
#    pypi.extra = https://kivy.org/downloads/simple/

#    -----------------------------------------------------------------------------
#    Recipes that will be used
