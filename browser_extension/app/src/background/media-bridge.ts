import {filenameFromUrl, truncate} from "../shared/utils";
import type {MediaAction, MediaItemOption, MediaPlaybackState} from "../shared/types";
import {MAIN_FRAME_ID} from "./constants";
import {sendMessageToTab, type TabMessageResult,} from "./chrome-helpers";

type RawMediaState = {
  count: number;
  src?: string[];
  currentTime?: number;
  duration?: number;
  time?: number;
  volume?: number;
  paused?: boolean;
  loop?: boolean;
  speed?: number;
  muted?: boolean;
};

type MediaTarget = {
  tabId: number;
  index: number;
};

type BuiltMediaPanelState = {
  mediaItems: MediaItemOption[];
  playbackState: MediaPlaybackState;
};

export function createMediaBridge() {
  let mediaControlTarget: MediaTarget = { tabId: 0, index: -1 };
  // Mirrors the last playbackState handed to the popup. Updated on every successful
  // buildPanelState poll; cleared on failure, no-tab, or tab removal. runAction reads it
  // to decide play-vs-pause (toggle_play) and whether to auto-unmute (set_volume).
  let lastPlaybackState: MediaPlaybackState | null = null;

  function createEmptyPlaybackState(message = "当前未检测到可控制媒体"): MediaPlaybackState {
    return {
      isAvailable: false,
      message,
      tabId: null,
      mediaIndex: -1,
      currentTime: 0,
      duration: 0,
      progress: 0,
      volume: 1,
      isPaused: true,
      shouldLoop: false,
      isMuted: false,
      speed: 1,
    };
  }

  function createEmptyMediaPanelState(message: string): BuiltMediaPanelState {
    return {
      mediaItems: [],
      playbackState: createEmptyPlaybackState(message),
    };
  }

  function createMediaItems(srcList: string[], count: number): MediaItemOption[] {
    return Array.from({ length: count }, (_unused, index) => {
      const src = srcList[index] ?? `media-${index + 1}`;
      return {
        index,
        label: truncate(filenameFromUrl(src) || src.split("/").pop() || src, 48),
      };
    });
  }

  function mediaFailureMessage(result: TabMessageResult<unknown>): string {
    switch (result.status) {
      case "no_receiver":
        return "当前页面的媒体桥接还没有准备好";
      case "runtime_error":
        return result.message || "读取媒体状态失败";
      case "no_response":
        return "页面没有返回媒体状态";
      default:
        return "当前页面未检测到可控制媒体";
    }
  }

  async function requestMediaState(tabId: number, index: number): Promise<TabMessageResult<RawMediaState>> {
    return sendMessageToTab<RawMediaState>(
      tabId,
      { Message: "getVideoState", index },
      { frameId: MAIN_FRAME_ID },
    );
  }

  // Fire-and-forget a cat-catch command to the content script. The content script executes
  // synchronously and never calls sendResponse, so no_response and runtime_error (port closed
  // before a response) are expected successes. Only no_receiver is a real failure — it means
  // the content script isn't loaded on this tab.
  async function sendMediaCommand(tabId: number, message: Record<string, unknown>): Promise<void> {
    const result = await sendMessageToTab<void>(tabId, message, { frameId: MAIN_FRAME_ID });
    if (result.status === "no_receiver") {
      throw new Error("当前页面的媒体桥接还没有准备好");
    }
  }

  function buildMediaMessage(action: MediaAction, value?: number | boolean): Record<string, unknown> | null {
    const index = mediaControlTarget.index;
    switch (action) {
      case "toggle_play":
        return { Message: lastPlaybackState?.isPaused ? "play" : "pause", index };
      case "set_speed":
        return { Message: "speed", speed: Number(value ?? 1), index };
      case "pip":
        return { Message: "pip", index };
      case "screenshot":
        return { Message: "screenshot", index };
      case "toggle_loop":
        return { Message: "loop", action: Boolean(value), index };
      case "toggle_muted":
        return { Message: "muted", action: Boolean(value), index };
      case "set_volume":
        return { Message: "setVolume", volume: Number(value ?? 1), index };
      case "set_time":
        return { Message: "setTime", time: Number(value ?? 0), index };
      case "fullscreen":
        // Owned by the popup (needs window.close); the SW never receives this action.
        return null;
      default: {
        const exhaustive: never = action;
        void exhaustive;
        return null;
      }
    }
  }

  async function buildPanelState(activeTabId: number | null): Promise<BuiltMediaPanelState> {
    const tabId = activeTabId;
    let mediaIndex = mediaControlTarget.tabId === tabId ? mediaControlTarget.index : 0;

    if (!tabId) {
      lastPlaybackState = null;
      return createEmptyMediaPanelState("当前没有可操作的标签页");
    }

    const result = await requestMediaState(tabId, mediaIndex >= 0 ? mediaIndex : 0);

    const state = result.response;
    if (result.status !== "ok" || !state?.count) {
      lastPlaybackState = null;
      return createEmptyMediaPanelState(mediaFailureMessage(result));
    }

    const count = Number(state.count ?? 0);
    mediaIndex = mediaIndex >= 0 && mediaIndex < count ? mediaIndex : 0;
    const srcList = Array.isArray(state.src) ? state.src : [];

    const playbackState: MediaPlaybackState = {
      isAvailable: true,
      message: "",
      tabId,
      mediaIndex,
      currentTime: Number(state.currentTime ?? 0),
      duration: Number(state.duration ?? 0),
      progress: Number(state.time ?? 0),
      volume: Number(state.volume ?? 1),
      isPaused: Boolean(state.paused ?? true),
      shouldLoop: Boolean(state.loop ?? false),
      isMuted: Boolean(state.muted ?? false),
      speed: Number(state.speed ?? 1),
    };

    lastPlaybackState = playbackState;

    if (mediaControlTarget.tabId !== tabId || mediaControlTarget.index !== mediaIndex) {
      mediaControlTarget = { tabId, index: mediaIndex };
    }

    return {
      mediaItems: createMediaItems(srcList, count),
      playbackState,
    };
  }

  async function runAction(action: MediaAction, value?: number | boolean): Promise<void> {
    const { tabId, index } = mediaControlTarget;
    if (!tabId || index < 0 || !lastPlaybackState) {
      throw new Error("当前没有可控制的媒体");
    }

    const message = buildMediaMessage(action, value);
    if (!message) {
      return;
    }

    // Auto-unmute when the user raises volume while muted.
    if (
      action === "set_volume"
      && typeof value === "number"
      && value > 0
      && lastPlaybackState.isMuted
    ) {
      await sendMediaCommand(tabId, { Message: "muted", action: false, index });
    }

    await sendMediaCommand(tabId, message);
  }

  function setMediaIndex(tabId: number, index: number) {
    mediaControlTarget = { tabId, index };
  }

  function onTabRemoved(tabId: number) {
    if (mediaControlTarget.tabId === tabId) {
      mediaControlTarget = { tabId: 0, index: -1 };
      lastPlaybackState = null;
    }
  }

  return {
    buildPanelState,
    runAction,
    onTabRemoved,
    setMediaIndex,
  };
}
