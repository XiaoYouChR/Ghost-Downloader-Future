import type {
    CommandResult,
    TaskSummary,
    PopupState,
    PopupView,
} from "./shared/types";
import type {PopupCommand} from "./shared/popup-protocol";
import {createDesktopBridge} from "./background/desktop-bridge";
import {createFeatureBridge} from "./background/feature-bridge";
import {createMediaBridge} from "./background/media-bridge";
import {createResourceBridge} from "./background/resource-bridge";
import {SHOULD_TAKE_DOWNLOADS_KEY, IS_MEDIA_BUTTON_ENABLED_KEY,} from "./background/constants";
import {
    cancelDownload,
    eraseDownloadFromHistory,
    findTab,
    loadLocalState,
    openActionPopup,
    queryTabs,
} from "./background/chrome-helpers";
import {onSendHeadersExtraInfoSpec, supportsDownloadDeterminingFilename,} from "./shared/browser";

const desktopBridge = createDesktopBridge();
const resourceBridge = createResourceBridge({
  sendDesktopRequest: (payload) => desktopBridge.sendRequest(payload),
});
const featureBridge = createFeatureBridge();
const mediaBridge = createMediaBridge();

let shouldTakeDownloads = true;
let isMediaButtonEnabled = true;

async function injectMediaButton(tabId: number) {
  if (!isMediaButtonEnabled) {
    return;
  }
  const tab = await findTab(tabId);
  if (!tab?.url || !/^https?:/i.test(tab.url)) {
    return;
  }

  try {
    await chrome.scripting.executeScript({
      files: ["page-media-overlay.js"],
      injectImmediately: false,
      target: { tabId, allFrames: true },
    });
  } catch {
    // chrome:// and similar reject injection.
  }
}

async function setMediaButtonEnabled(enabled: boolean) {
  isMediaButtonEnabled = enabled;
  await chrome.storage.local.set({ [IS_MEDIA_BUTTON_ENABLED_KEY]: enabled });

  const tabs = await queryTabs({});
  for (const tab of tabs) {
    if (!tab.id || !tab.url || !/^https?:/i.test(tab.url)) {
      continue;
    }
    chrome.tabs.sendMessage(tab.id, {
      type: "media_button_set_enabled",
      enabled,
    }, () => {
      const lastError = chrome.runtime.lastError;
      if (enabled && lastError && tab.id) {
        void injectMediaButton(tab.id);
      }
    });
  }
}

function buildTaskCounters(tasks: TaskSummary[]) {
  return {
    total: tasks.length,
    active: tasks.filter((task) => task.status !== "completed").length,
    completed: tasks.filter((task) => task.status === "completed").length,
  };
}

async function buildPopupState(options: {
  preferredTabId?: number | null;
  currentView?: PopupView;
} = {}): Promise<PopupState> {
  const activeTabId = await resourceBridge.currentTabId(options.preferredTabId ?? null);
  const activeTab = activeTabId != null ? await findTab(activeTabId) : null;
  const desktopState = desktopBridge.buildSnapshot();
  const resourceState = resourceBridge.buildPopupStateData(activeTabId, activeTab);

  const mediaPanelState = await mediaBridge.buildPanelState(
    options.currentView === "advanced" ? activeTabId : null,
  );

  return {
    connectionState: desktopState.connectionState,
    connectionMessage: desktopState.connectionMessage,
    desktopVersion: desktopState.desktopVersion,
    token: desktopState.token,
    serverUrl: desktopState.serverUrl,
    shouldTakeDownloads,
    isMediaButtonEnabled,
    tasks: desktopState.tasks,
    taskCounters: buildTaskCounters(desktopState.tasks),
    tabId: activeTabId,
    featureStates: featureBridge.createFeatureStateMap(activeTabId),
    mediaItems: mediaPanelState.mediaItems,
    mediaPlaybackState: mediaPanelState.playbackState,
    ...resourceState,
  };
}

async function setupBackground() {
  const localState = await loadLocalState<{
    [SHOULD_TAKE_DOWNLOADS_KEY]: boolean;
    [IS_MEDIA_BUTTON_ENABLED_KEY]: boolean;
  }>({
    [SHOULD_TAKE_DOWNLOADS_KEY]: true,
    [IS_MEDIA_BUTTON_ENABLED_KEY]: true,
  });

  shouldTakeDownloads = Boolean(localState[SHOULD_TAKE_DOWNLOADS_KEY] ?? true);
  isMediaButtonEnabled = Boolean(localState[IS_MEDIA_BUTTON_ENABLED_KEY] ?? true);

  try {
    const selfInfo = await chrome.management.getSelf();
    desktopBridge.setInstallType(selfInfo.installType);
  } catch {
    desktopBridge.setInstallType("normal");
  }

  await desktopBridge.loadPersistentState();
  await resourceBridge.loadPersistentState();
  await featureBridge.loadPersistentState();
  const activeTabId = await resourceBridge.currentTabId();
  if (activeTabId != null) {
    void injectMediaButton(activeTabId);
  }

  if (desktopBridge.buildSnapshot().token) {
    void desktopBridge.connect();
  }

  desktopBridge.setupReconnectAlarm();
}

chrome.alarms.onAlarm.addListener((alarm) => {
  desktopBridge.onReconnectAlarm(alarm);
});

chrome.runtime.onConnect.addListener((port) => {
  if (port.name === "HeartBeat") {
    port.postMessage("HeartBeat");
  }
});

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local") {
    return;
  }
  desktopBridge.onLocalStorageChanged(changes);
  if (changes[SHOULD_TAKE_DOWNLOADS_KEY]) {
    shouldTakeDownloads = Boolean(changes[SHOULD_TAKE_DOWNLOADS_KEY].newValue ?? true);
  }
  if (changes[IS_MEDIA_BUTTON_ENABLED_KEY]) {
    isMediaButtonEnabled = Boolean(changes[IS_MEDIA_BUTTON_ENABLED_KEY].newValue ?? true);
  }
});

chrome.tabs.onActivated.addListener((activeInfo) => {
  void resourceBridge.setLastActiveTab(activeInfo.tabId);
  void injectMediaButton(activeInfo.tabId);
});

chrome.windows.onFocusChanged.addListener((windowId) => {
  if (windowId === chrome.windows.WINDOW_ID_NONE) {
    return;
  }
  void resourceBridge.refreshActiveTabFromBrowser().then((tabId) => {
    if (tabId != null) {
      void injectMediaButton(tabId);
    }
  });
});

chrome.tabs.onRemoved.addListener((tabId) => {
  resourceBridge.onTabRemoved(tabId);
  mediaBridge.onTabRemoved(tabId);
  featureBridge.onTabRemoved(tabId);
});

chrome.webNavigation.onCommitted.addListener((details) => {
  resourceBridge.onNavigationCommitted(details);
  featureBridge.onNavigationCommitted(details);
});

chrome.webRequest.onSendHeaders.addListener(
  (details) => {
    resourceBridge.onRequestHeaders(details);
    void resourceBridge.captureRequestResource(details);
  },
  { urls: ["<all_urls>"] },
  onSendHeadersExtraInfoSpec(),
);

chrome.webRequest.onResponseStarted.addListener(
  (details) => {
    void resourceBridge.captureNetworkResource(details);
  },
  { urls: ["<all_urls>"] },
  ["responseHeaders"],
);

async function takeBrowserDownload(
  downloadItem: chrome.downloads.DownloadItem,
  options: { eraseFromHistory?: boolean } = {},
) {
  const finalUrl = downloadItem.finalUrl || downloadItem.url;
  if (!shouldTakeDownloads || !desktopBridge.isReady() || !/^https?:/i.test(finalUrl)) {
    return;
  }

  try {
    await cancelDownload(downloadItem.id);
    if (options.eraseFromHistory) {
      await eraseDownloadFromHistory(downloadItem.id);
    }
  } catch {
    // Cleanup failed but the browser will still finish the download as fallback.
  }

  await resourceBridge.routeBrowserDownload(downloadItem);
}

function sendReply(sendResponse: (response?: unknown) => void, response: Promise<unknown>) {
  void response.then(sendResponse);
  return true;
}

if (supportsDownloadDeterminingFilename()) {
  chrome.downloads.onDeterminingFilename.addListener((downloadItem, suggest) => {
    suggest();
    void takeBrowserDownload(downloadItem);
  });
} else if (chrome.downloads.onCreated?.addListener) {
  chrome.downloads.onCreated.addListener((downloadItem) => {
    void takeBrowserDownload(downloadItem, { eraseFromHistory: true });
  });
}

// The typed receiver half of the popup command seam (shared/popup-protocol.ts): one
// exhaustive switch over the command union. Each case narrows the command to its own shape
// (no cast); the never-typed default makes a missing case a compile error.
async function runPopupCommand(command: PopupCommand): Promise<PopupState | CommandResult> {
  switch (command.type) {
    case "popup_get_state":
      return buildPopupState({
        preferredTabId: typeof command.tabId === "number" ? command.tabId : null,
        currentView: command.view,
      });
    case "popup_set_token":
      await desktopBridge.setToken(command.token.trim());
      return buildPopupState({ currentView: command.view });
    case "popup_set_server_url":
      await desktopBridge.setServerUrl(command.serverUrl);
      return buildPopupState({ currentView: command.view });
    case "popup_refresh_connection":
      await desktopBridge.connect(true);
      return buildPopupState({ currentView: command.view });
    case "popup_set_take_downloads":
      shouldTakeDownloads = command.enabled;
      await chrome.storage.local.set({ [SHOULD_TAKE_DOWNLOADS_KEY]: shouldTakeDownloads });
      return buildPopupState({ currentView: command.view });
    case "popup_set_media_button":
      await setMediaButtonEnabled(command.enabled);
      return buildPopupState({ currentView: command.view });
    case "popup_set_media_index":
      await mediaBridge.setMediaIndex(command.tabId, command.index);
      return buildPopupState({ currentView: "advanced" });
    case "popup_request_pairing":
      void desktopBridge.requestPairing().catch(() => {
        // The bridge snapshot carries the user-facing pairing failure message.
      });
      return { ok: true, message: "请确认配对" };
    case "popup_task_action":
      try {
        return await desktopBridge.sendRequest<CommandResult>({
          type: "task_action",
          taskId: command.taskId,
          action: command.action,
        });
      } catch (error) {
        return { ok: false, message: error instanceof Error ? error.message : "任务操作失败" };
      }
    case "popup_send_resource":
      return resourceBridge.sendResource(command.resourceId);
    case "popup_merge_resources":
      return resourceBridge.mergeResources(command.resourceIds);
    case "popup_toggle_feature":
      try {
        const infoMessage = await featureBridge.toggleFeature(command.feature, command.tabId);
        return { ok: true, message: infoMessage };
      } catch (error) {
        return { ok: false, message: error instanceof Error ? error.message : "功能切换失败" };
      }
    case "popup_media_action":
      try {
        await mediaBridge.runAction(command.action, command.value);
        return { ok: true, message: "" };
      } catch (error) {
        return { ok: false, message: error instanceof Error ? error.message : "媒体操作失败" };
      }
    default:
      return unknownPopupCommand(command);
  }
}

// Reached only by a popup_ message whose type is not a known command. The `never` parameter
// makes the switch above exhaustive at compile time; at runtime it returns a structured
// error instead of throwing, so the caller still gets a response.
function unknownPopupCommand(command: never): CommandResult {
  return { ok: false, message: `未知命令: ${(command as { type?: string }).type ?? ""}` };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || typeof message !== "object") {
    return;
  }

  if (message.Message === "addMedia" && typeof message.url === "string") {
    void resourceBridge.capturePageResource(sender, {
      url: message.url,
      href: message.href,
      mime: message.mime,
      ext: message.extraExt,
      requestHeaders: message.requestHeaders,
    });
    sendResponse("ok");
    return true;
  }

  if (typeof message.type !== "string") {
    return;
  }

  if (message.type === "bridge_page_command") {
    void featureBridge.onBridgeScriptCommand(message.payload, sender);
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === "page_download_media") {
    return sendReply(sendResponse, resourceBridge.downloadPageMedia(sender, {
      selection: message.selection,
      href: String(message.href ?? ""),
      title: String(message.title ?? ""),
    }));
  }

  if (message.type === "page_media_button_state") {
    sendResponse({ enabled: isMediaButtonEnabled });
    return;
  }

  // popup_ commands are privileged (set token / server URL / merge resources). A page can
  // forward arbitrary runtime messages through cat-catch's content script, so the sender —
  // not just the type prefix — is the guard: only the extension's own popup (a
  // chrome-extension:// page, never a tab) may reach the dispatcher. That lets the cast trust
  // the payload, since the popup is the sole, typed caller.
  if (message.type.startsWith("popup_")) {
    if (!sender.url?.startsWith("chrome-extension://")) { return; }
    return sendReply(sendResponse, runPopupCommand(message as PopupCommand));
  }
});

chrome.runtime.onSuspend.addListener(() => {
  void resourceBridge.flushState();
});

void setupBackground();
