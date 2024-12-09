using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;
using System.Linq;

public class Builder
{
    public static void Build()
    {
        string[] scenes = new[] { "Assets/Scenes/SampleScene.unity" };
        
        BuildPlayerOptions options = new BuildPlayerOptions
        {
            scenes = scenes,
            locationPathName = "Builds/" + GetBuildPath(),
            target = GetBuildTarget(),
            options = BuildOptions.None
        };

        BuildReport report = BuildPipeline.BuildPlayer(options);
        if (report.summary.result == BuildResult.Succeeded)
        {
            Debug.Log("Build succeeded");
            EditorApplication.Exit(0);
        }
        else
        {
            Debug.LogError("Build failed");
            EditorApplication.Exit(1);
        }
    }

    private static BuildTarget GetBuildTarget()
    {
        #if UNITY_EDITOR_OSX
            return BuildTarget.StandaloneOSX;
        #elif UNITY_EDITOR_LINUX
            return BuildTarget.StandaloneLinux64;
        #else
            return BuildTarget.StandaloneWindows64;
        #endif
    }

    private static string GetBuildPath()
    {
        #if UNITY_EDITOR_OSX
            return "Sim.app";
        #elif UNITY_EDITOR_LINUX
            return "Sim.x86_64";
        #else
            return "Sim.exe";
        #endif
    }
}
