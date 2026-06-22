# Add project specific ProGuard rules here.
# https://developer.android.com/guide/developing/tools/proguard.html

-keepattributes *Annotation*,Signature,InnerClasses,EnclosingMethod

-keepclasseswithmembernames class * {
    native <methods>;
}

-keep class io.github.dovecoteescapee.byedpi.core.ByeDpiProxy { *; }
-keep class io.github.dovecoteescapee.byedpi.core.TProxyService { *; }
-keep interface io.github.dovecoteescapee.byedpi.core.TgWsProxyLibrary { *; }

-keep class com.sun.jna.** { *; }
-keep interface com.sun.jna.** { *; }
-dontwarn com.sun.jna.**

-keep class androidx.lifecycle.** { *; }
-keep class * extends androidx.lifecycle.ViewModel { *; }

-keepclassmembers class * implements android.os.Parcelable {
    public static final ** CREATOR;
}
