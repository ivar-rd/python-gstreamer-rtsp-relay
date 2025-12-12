import os
import sys
import threading
from urllib.parse import urlparse
from pathlib import Path

IS_FROZEN = getattr(sys, 'frozen', False)
GSTREAMER_ROOT = r"C:\\Program Files\\gstreamer\\1.0\\msvc_x86_64" 
GSTREAMER_BIN_PATH = os.path.join(GSTREAMER_ROOT, "bin")

if IS_FROZEN:
    if sys.version_info >= (3, 8):
        if os.path.isdir(GSTREAMER_BIN_PATH):
            os.add_dll_directory(GSTREAMER_BIN_PATH)

    os.environ['PATH'] = GSTREAMER_BIN_PATH + os.pathsep + os.environ.get('PATH', '')
    os.environ['GST_PLUGIN_PATH'] = GSTREAMER_PLUGINS
    os.environ['GI_TYPELIB_PATH'] = GSTREAMER_GIR
    print("GStreamer 環境設定完成。")
else:
    print("運行在腳本模式，依賴系統或虛擬環境的 GStreamer 配置。")
    if sys.version_info >= (3, 8):
        os.add_dll_directory(GSTREAMER_BIN_PATH) 
    os.environ['PATH'] = GSTREAMER_BIN_PATH + os.pathsep + os.environ.get('PATH', '')

# =========================================================================
# 2. GStreamer
# =========================================================================
try:
    import gi
    gi.require_version('GLib', '2.0')
    gi.require_version('GObject', '2.0') 
    gi.require_version('Gst', '1.0')
    gi.require_version('GstRtspServer', '1.0')
    from gi.repository import GObject, Gst, GstRtspServer, GLib

    Gst.init(None)
except Exception as e:
    if IS_FROZEN:
        import traceback
        traceback.print_exc() 
    
    print(f"\n致命錯誤：GStreamer/PyGObject 載入失敗！錯誤訊息: {e}")
    print("\n請檢查 main.spec 中的路徑配置是否正確複製了所有 GStreamer DLLs 和資源。")
    sys.exit(1)

class RTSPProxyFactory(GstRtspServer.RTSPMediaFactory):
    def __init__(self, upstream_rtsp_url, **kwargs):
        super().__init__(**kwargs)
        self.upstream_rtsp_url = upstream_rtsp_url

    def do_create_element(self, url):
        rtsp_pipeline = f"""
            rtspsrc location={self.upstream_rtsp_url} protocols=tcp latency=100 ! 
            rtph264depay ! h264parse ! 
            rtph264pay name=pay0 pt=96
        """
        
        # 設置 Pipeline
        return Gst.parse_launch(rtsp_pipeline)

def run_server():
    #MediaMTX url
    upstream_url = "rtsp://127.0.0.1.:554/live/ch1"

    server_port = 8555
    mount_point = "/test"

    server = GstRtspServer.RTSPServer.new()
    server.set_service(str(server_port))
    
    factory = RTSPProxyFactory(upstream_url)
    factory.set_shared(True)
    
    mount_points = server.get_mount_points()
    mount_points.add_factory(mount_point, factory)
    
    loop = GLib.MainLoop.new(None, False)

    print("\n" + "="*50)
    print("RTSP 代理伺服器已啟動")
    print(f"  -> 上游 RTSP 源: {upstream_url}")
    print(f"  -> 代理埠口: {server_port}")
    print(f"  -> 客戶端連接 URL: rtsp://<IP-ADDRESS>:{server_port}{mount_point}")
    print("="*50 + "\n")
    
    try:
        loop.run()
    except KeyboardInterrupt:
        print("伺服器關閉中...")
    finally:
        loop.quit()

if __name__ == '__main__':
    run_server()