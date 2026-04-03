#if UNITY_EDITOR
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using System;
using System.IO;
using System.Linq;

namespace UnityCLI
{
    /// <summary>
    /// Editor utility invoked by unity-cli to capture UI screenshots.
    /// Installed automatically via `unity-cli scene screenshot`.
    /// </summary>
    public static class Capture
    {
        [MenuItem("UnityCLI/Capture Screenshot")]
        public static void CaptureScreenshot()
        {
            // Parse command-line arguments
            string[] args = Environment.GetCommandLineArgs();
            string outputPath = GetArg(args, "-outputPath", "screenshot.png");
            string scenePath = GetArg(args, "-scenePath", "");
            int width = int.Parse(GetArg(args, "-width", "1920"));
            int height = int.Parse(GetArg(args, "-height", "1080"));

            try
            {
                // Open scene if specified
                if (!string.IsNullOrEmpty(scenePath))
                {
                    EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
                }

                // Ensure output directory exists
                string dir = Path.GetDirectoryName(outputPath);
                if (!string.IsNullOrEmpty(dir) && !Directory.Exists(dir))
                {
                    Directory.CreateDirectory(dir);
                }

                RenderAndSave(outputPath, width, height);
                Debug.Log($"[UnityCLI] Screenshot saved: {outputPath}");
            }
            catch (Exception ex)
            {
                Debug.LogError($"[UnityCLI] Capture failed: {ex.Message}");
                EditorApplication.Exit(1);
                return;
            }

            EditorApplication.Exit(0);
        }

        /// <summary>
        /// Render the current scene to a PNG file.
        /// Handles both UI Canvas elements and regular 3D/2D scenes.
        /// </summary>
        static void RenderAndSave(string outputPath, int width, int height)
        {
            // Create RenderTexture
            RenderTexture rt = new RenderTexture(width, height, 24, RenderTextureFormat.ARGB32);
            rt.antiAliasing = 4;
            rt.Create();

            // Find or create a render camera
            Camera cam = Camera.main;
            bool createdCamera = false;

            if (cam == null)
            {
                GameObject camObj = new GameObject("__UnityCLI_Camera");
                cam = camObj.AddComponent<Camera>();
                cam.backgroundColor = new Color(0.15f, 0.15f, 0.15f, 1f);
                cam.clearFlags = CameraClearFlags.SolidColor;
                cam.orthographic = true;
                cam.orthographicSize = 5;
                createdCamera = true;
            }

            // Handle UI Canvases — switch Overlay canvases to Camera mode for rendering
            Canvas[] canvases = UnityEngine.Object.FindObjectsByType<Canvas>(FindObjectsSortMode.None);
            var originalModes = new (Canvas canvas, RenderMode mode, Camera worldCam)[canvases.Length];

            for (int i = 0; i < canvases.Length; i++)
            {
                originalModes[i] = (canvases[i], canvases[i].renderMode, canvases[i].worldCamera);

                if (canvases[i].renderMode == RenderMode.ScreenSpaceOverlay)
                {
                    canvases[i].renderMode = RenderMode.ScreenSpaceCamera;
                    canvases[i].worldCamera = cam;
                }
            }

            // Force layout rebuild for UI elements
            Canvas.ForceUpdateCanvases();

            // Render
            RenderTexture prevActive = RenderTexture.active;
            cam.targetTexture = rt;
            cam.Render();

            // Read pixels
            RenderTexture.active = rt;
            Texture2D tex = new Texture2D(width, height, TextureFormat.RGBA32, false);
            tex.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            tex.Apply();

            // Save PNG
            byte[] pngBytes = tex.EncodeToPNG();
            File.WriteAllBytes(outputPath, pngBytes);

            // Cleanup — restore original canvas modes
            for (int i = 0; i < canvases.Length; i++)
            {
                if (canvases[i] != null)
                {
                    canvases[i].renderMode = originalModes[i].mode;
                    canvases[i].worldCamera = originalModes[i].worldCam;
                }
            }

            RenderTexture.active = prevActive;
            cam.targetTexture = null;
            UnityEngine.Object.DestroyImmediate(tex);
            rt.Release();
            UnityEngine.Object.DestroyImmediate(rt);

            if (createdCamera)
            {
                UnityEngine.Object.DestroyImmediate(cam.gameObject);
            }
        }

        static string GetArg(string[] args, string name, string defaultValue)
        {
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == name)
                    return args[i + 1];
            }
            return defaultValue;
        }
    }
}
#endif
