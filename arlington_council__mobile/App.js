import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActivityIndicator,
  Image,
  I18nManager,
  Modal,
  Platform,
  Pressable,
  RefreshControl,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { WebView } from "react-native-webview";

import {
  DEFAULT_API_BASE_URL,
  cleanBaseUrl,
  getBootstrap,
  getDonationCampaigns,
  getProjects,
  getProposals,
  submitDonationPledge,
  submitSuggestion,
  submitVolunteer
} from "./src/api";
import { statusLabel, t } from "./src/i18n";
import { compactShadow, palette, shadow } from "./src/theme";

const logo = require("./assets/arlington-civic-mark.png");
const bottomTabs = ["home", "projects", "donations", "other"];

function roleFromPath(path = "", explicitRole = "") {
  if (explicitRole) return explicitRole;
  if (/\/admin(\/|$)/.test(path)) return "admin";
  if (/\/tracker(\/|$)/.test(path)) return "tracker";
  if (/\/council(\/|$)/.test(path)) return "council";
  if (/\/news-desk(\/|$)/.test(path)) return "news";
  return "";
}

function formatDate(value, locale) {
  if (!value) return t(locale, "notScheduled");
  try {
    return new Date(value).toLocaleDateString(locale === "es" ? "es-US" : "en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  } catch {
    return t(locale, "notScheduled");
  }
}

function money(value, currency) {
  const amount = Number(value || 0);
  return `${amount.toLocaleString(undefined, { maximumFractionDigits: 0 })} ${currency || ""}`.trim();
}

function languageStyles(locale) {
  const isRtl = false;
  return {
    isRtl,
    row: isRtl ? styles.rowReverse : styles.row,
    align: isRtl ? styles.alignEnd : styles.alignStart,
    text: isRtl ? styles.textRtl : styles.textLtr
  };
}

export default function App() {
  const [locale, setLocale] = useState("en");
  const [activeTab, setActiveTab] = useState("home");
  const [optionsOpen, setOptionsOpen] = useState(false);
  const [webPage, setWebPage] = useState(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [workspacePath, setWorkspacePath] = useState("");
  const [authRole, setAuthRole] = useState("");
  const [apiBaseUrl] = useState(cleanBaseUrl(DEFAULT_API_BASE_URL));
  const [data, setData] = useState({
    stats: {},
    announcements: [],
    news: [],
    recentProjects: [],
    usefulSites: [],
    projects: [],
    campaigns: [],
    proposals: []
  });
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [suggestion, setSuggestion] = useState({
    target_type: "council",
    project_id: "",
    name: "",
    contact: "",
    title: "",
    body: ""
  });
  const [volunteerProjectId, setVolunteerProjectId] = useState(null);
  const [volunteerForm, setVolunteerForm] = useState({ name: "", additional_info: "" });
  const [pledgeCampaignId, setPledgeCampaignId] = useState(null);
  const [pledgeForm, setPledgeForm] = useState({
    donor_name: "",
    amount: "",
    new_group_name: "",
    message: "",
    display_name: true
  });
  const dir = languageStyles(locale);

  useEffect(() => {
    I18nManager.allowRTL(false);
  }, []);

  const loadAll = useCallback(async (mode = "load") => {
    if (mode === "refresh") setRefreshing(true);
    else setLoading(true);
    setError("");
    try {
      const [bootstrap, projects, donations, proposals] = await Promise.all([
        getBootstrap(apiBaseUrl, locale),
        getProjects(apiBaseUrl, locale),
        getDonationCampaigns(apiBaseUrl, locale),
        getProposals(apiBaseUrl, locale)
      ]);
      setData({
        stats: bootstrap.stats || {},
        announcements: bootstrap.announcements || [],
        news: bootstrap.news || [],
        recentProjects: bootstrap.recent_projects || [],
        usefulSites: bootstrap.useful_sites || [],
        projects: projects.projects || [],
        campaigns: donations.campaigns || [],
        proposals: proposals.proposals || []
      });
    } catch (err) {
      setError(err.message || t(locale, "errorTitle"));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [apiBaseUrl, locale]);

  useEffect(() => {
    loadAll();
  }, [loadAll]);

  const selectedProjectOptions = useMemo(() => data.projects.slice(0, 8), [data.projects]);
  const currentRole = authRole || roleFromPath(workspacePath);

  const openInAppWeb = useCallback((url, title, options = {}) => {
    if (!url) return;
    setOptionsOpen(false);
    setWebPage({ url, title: title || t(locale, "websitePage"), ...options });
  }, [locale]);

  const goToTab = useCallback((tab) => {
    setWebPage(null);
    setActiveTab(tab);
  }, []);

  const handleAuthStatus = useCallback((authenticated, path = "", role = "") => {
    setIsLoggedIn(Boolean(authenticated));
    if (authenticated && path) {
      setWorkspacePath(path);
    }
    if (authenticated) {
      setAuthRole(roleFromPath(path, role));
    }
    if (!authenticated) {
      setWorkspacePath("");
      setAuthRole("");
    }
    if (!authenticated && webPage?.action === "logout") {
      setWebPage(null);
      setNotice(t(locale, "loggedOut"));
    }
  }, [locale, webPage?.action]);

  async function sendSuggestion() {
    setNotice("");
    try {
      const payload = {
        ...suggestion,
        project_id: suggestion.target_type === "project_tracker" ? suggestion.project_id : null
      };
      const response = await submitSuggestion(apiBaseUrl, locale, payload);
      setNotice(response.message);
      setSuggestion({ target_type: "council", project_id: "", name: "", contact: "", title: "", body: "" });
      await loadAll("refresh");
    } catch (err) {
      setNotice(err.message);
    }
  }

  async function sendVolunteer(projectId) {
    setNotice("");
    try {
      const response = await submitVolunteer(apiBaseUrl, locale, projectId, volunteerForm);
      setNotice(response.message);
      setVolunteerProjectId(null);
      setVolunteerForm({ name: "", additional_info: "" });
      await loadAll("refresh");
    } catch (err) {
      setNotice(err.message);
    }
  }

  async function sendPledge(campaignId) {
    setNotice("");
    try {
      const response = await submitDonationPledge(apiBaseUrl, locale, campaignId, {
        ...pledgeForm,
        attribution_type: pledgeForm.new_group_name ? "group" : "independent"
      });
      setNotice(`${response.message} ${t(locale, "reference")}: ${response.payment_reference}`);
      setPledgeCampaignId(null);
      setPledgeForm({ donor_name: "", amount: "", new_group_name: "", message: "", display_name: true });
      await loadAll("refresh");
    } catch (err) {
      setNotice(err.message);
    }
  }

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.safe} edges={["bottom"]}>
      <StatusBar barStyle="light-content" backgroundColor={palette.greenDeep} />
      <View style={styles.appFrame}>
        <Header
          locale={locale}
          setLocale={(nextLocale) => {
            setLocale(nextLocale);
            setNotice("");
          }}
          dir={dir}
        />
        <AuthProbe locale={locale} apiBaseUrl={apiBaseUrl} onAuthChange={handleAuthStatus} />
        <View style={styles.contentFrame}>
          {notice ? <Text style={[styles.notice, dir.text]}>{notice}</Text> : null}
          {webPage ? (
            <WebScreen locale={locale} page={webPage} close={() => setWebPage(null)} dir={dir} onAuthChange={handleAuthStatus} />
          ) : loading ? (
            <View style={styles.loadingPanel}>
              <ActivityIndicator color={palette.green} size="large" />
              <Text style={[styles.muted, dir.text]}>{t(locale, "loading")}</Text>
            </View>
          ) : (
            <ScrollView
              contentContainerStyle={styles.scrollContent}
              keyboardShouldPersistTaps="handled"
              refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => loadAll("refresh")} tintColor={palette.green} />}
            >
              {error ? <ErrorPanel locale={locale} message={error} onRetry={() => loadAll()} dir={dir} /> : null}
              {activeTab === "home" ? <HomeScreen locale={locale} data={data} dir={dir} openWeb={openInAppWeb} /> : null}
              {activeTab === "projects" ? (
                <ProjectsScreen
                  locale={locale}
                  projects={data.projects}
                  dir={dir}
                  volunteerProjectId={volunteerProjectId}
                  setVolunteerProjectId={setVolunteerProjectId}
                  volunteerForm={volunteerForm}
                  setVolunteerForm={setVolunteerForm}
                  onVolunteer={sendVolunteer}
                  openWeb={openInAppWeb}
                />
              ) : null}
              {activeTab === "donations" ? (
                <DonationsScreen
                  locale={locale}
                  campaigns={data.campaigns}
                  dir={dir}
                  pledgeCampaignId={pledgeCampaignId}
                  setPledgeCampaignId={setPledgeCampaignId}
                  pledgeForm={pledgeForm}
                  setPledgeForm={setPledgeForm}
                  onPledge={sendPledge}
                  openWeb={openInAppWeb}
                />
              ) : null}
              {activeTab === "proposals" ? <ProposalsScreen locale={locale} proposals={data.proposals} dir={dir} openWeb={openInAppWeb} /> : null}
              {activeTab === "suggest" ? (
                <SuggestionsScreen
                  locale={locale}
                  projects={selectedProjectOptions}
                  suggestion={suggestion}
                  setSuggestion={setSuggestion}
                  onSubmit={sendSuggestion}
                  dir={dir}
                />
              ) : null}
              {activeTab === "more" ? (
                <MoreScreen
                  locale={locale}
                  sites={data.usefulSites}
                  openWeb={openInAppWeb}
                  dir={dir}
                />
              ) : null}
            </ScrollView>
          )}
        </View>
        <TabBar
          locale={locale}
          activeTab={activeTab}
          setActiveTab={goToTab}
          openOptions={() => setOptionsOpen(true)}
        />
        <OptionsSheet
          visible={optionsOpen}
          locale={locale}
          dir={dir}
          close={() => setOptionsOpen(false)}
          selectTab={(tab) => {
            goToTab(tab);
            setOptionsOpen(false);
          }}
          openLogin={() => {
            openInAppWeb(`${apiBaseUrl}/${locale}/login`, t(locale, "login"));
          }}
          openWorkspace={() => {
            openInAppWeb(`${apiBaseUrl}/${locale}/dashboard`, t(locale, "workspace"));
          }}
          openRoleTool={(path, label) => {
            openInAppWeb(`${apiBaseUrl}/${locale}${path}`, label);
          }}
          openLogout={() => {
            openInAppWeb(`${apiBaseUrl}/${locale}/dashboard`, t(locale, "logout"), { action: "logout" });
          }}
          isLoggedIn={isLoggedIn}
          role={currentRole}
        />
      </View>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

function Header({ locale, setLocale, dir }) {
  return (
    <View style={styles.header}>
      <View style={[styles.headerTop, dir.row]}>
        <View style={[styles.brandCluster, dir.row]}>
          <View style={styles.logoMark}>
            <Image source={logo} style={styles.logoImage} resizeMode="contain" />
          </View>
          <View style={[styles.brandCopy, dir.align]}>
            <Text style={[styles.brandTitle, dir.text]} numberOfLines={1} allowFontScaling={false}>{t(locale, "appNameShort")}</Text>
            <Text style={[styles.brandSub, dir.text]} numberOfLines={1} allowFontScaling={false}>{t(locale, "appSubtitle")}</Text>
          </View>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={locale === "en" ? "Switch to Spanish" : "Switch to English"}
          hitSlop={10}
          style={styles.langButton}
          onPress={() => setLocale(locale === "en" ? "es" : "en")}
        >
          <Text style={styles.langButtonText} allowFontScaling={false}>{locale === "en" ? "ES" : "EN"}</Text>
        </Pressable>
      </View>
    </View>
  );
}

function TabBar({ locale, activeTab, setActiveTab, openOptions }) {
  const selectedTab = ["suggest", "proposals", "more"].includes(activeTab) ? "other" : activeTab;
  return (
    <View style={styles.tabWrap}>
      <View style={styles.tabScroller}>
        {bottomTabs.map((tab) => (
          <Pressable
            key={tab}
            accessibilityRole="button"
            onPress={() => {
              if (tab === "other") openOptions();
              else setActiveTab(tab);
            }}
            style={[styles.tab, selectedTab === tab && styles.tabActive]}
          >
            <Text style={[styles.tabText, selectedTab === tab && styles.tabTextActive]} numberOfLines={1} allowFontScaling={false}>
              {t(locale, tab)}
            </Text>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

function OptionsSheet({ visible, locale, dir, close, selectTab, openLogin, openWorkspace, openRoleTool, openLogout, isLoggedIn, role }) {
  const roleOptions = isLoggedIn
    ? role === "admin"
      ? [
          { key: "adminPanel", title: t(locale, "adminPanel"), body: t(locale, "adminPanelHelp"), action: () => openRoleTool("/admin", t(locale, "adminPanel")) },
          { key: "manageUsers", title: t(locale, "manageUsers"), body: t(locale, "manageUsersHelp"), action: () => openRoleTool("/manage_users", t(locale, "manageUsers")) },
          { key: "donationAdmin", title: t(locale, "donationAdmin"), body: t(locale, "donationAdminHelp"), action: () => openRoleTool("/admin/donations", t(locale, "donationAdmin")) },
          { key: "donationDashboard", title: t(locale, "donationDashboard"), body: t(locale, "donationDashboardHelp"), action: () => openRoleTool("/admin/donations/dashboard", t(locale, "donationDashboard")) },
          { key: "siteLinks", title: t(locale, "siteLinks"), body: t(locale, "siteLinksHelp"), action: () => openRoleTool("/admin/site-links", t(locale, "siteLinks")) },
          { key: "homeContent", title: t(locale, "homeContent"), body: t(locale, "homeContentHelp"), action: () => openRoleTool("/home-content", t(locale, "homeContent")) },
          { key: "suggestionInbox", title: t(locale, "suggestionInbox"), body: t(locale, "suggestionInboxHelp"), action: () => openRoleTool("/suggestions/inbox", t(locale, "suggestionInbox")) },
          { key: "profile", title: t(locale, "profile"), body: t(locale, "profileHelp"), action: () => openRoleTool("/profile/edit", t(locale, "profile")) }
        ]
      : [
          { key: "workspace", title: t(locale, "workspace"), body: t(locale, "workspaceHelp"), action: openWorkspace }
        ]
    : [];

  const options = [
    { key: "suggest", title: t(locale, "suggestionTitle"), body: t(locale, "suggestionHelp"), action: () => selectTab("suggest") },
    { key: "proposals", title: t(locale, "publicProposals"), body: t(locale, "proposalsHelp"), action: () => selectTab("proposals") },
    { key: "usefulSites", title: t(locale, "usefulSites"), body: t(locale, "usefulSitesHelp"), action: () => selectTab("more") },
    ...roleOptions,
    isLoggedIn
      ? { key: "logout", title: t(locale, "logout"), body: t(locale, "logoutHelp"), action: openLogout }
      : { key: "login", title: t(locale, "login"), body: t(locale, "loginHelp"), action: openLogin }
  ].filter(Boolean);

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={close}>
      <View style={styles.sheetRoot}>
        <Pressable style={styles.sheetBackdrop} onPress={close} />
        <View style={styles.sheetPanel}>
          <View style={[styles.sheetHeader, dir.row]}>
            <View style={[styles.sheetHandleBlock, dir.align]}>
              <View style={styles.sheetHandle} />
              <Text style={[styles.sheetTitle, dir.text]}>{t(locale, "other")}</Text>
              <Text style={[styles.sheetSubtitle, dir.text]}>{t(locale, "otherHelp")}</Text>
            </View>
            <Pressable accessibilityRole="button" hitSlop={10} style={styles.sheetClose} onPress={close}>
              <Text style={styles.sheetCloseText} allowFontScaling={false}>X</Text>
            </Pressable>
          </View>
          <ScrollView contentContainerStyle={styles.sheetScroll} showsVerticalScrollIndicator={false}>
            {options.map((option) => (
              <Pressable key={option.key} style={[styles.optionCard, dir.row]} onPress={option.action}>
                <View style={styles.optionIcon}>
                  <Text style={styles.optionIconText} allowFontScaling={false}>{option.title.slice(0, 1)}</Text>
                </View>
                <View style={[styles.optionTextBlock, dir.align]}>
                  <Text style={[styles.optionTitle, dir.text]}>{option.title}</Text>
                  <Text style={[styles.optionBody, dir.text]}>{option.body}</Text>
                </View>
              </Pressable>
            ))}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const webChromeScript = `
  (function () {
    function roleFromPath(path) {
      if (/\\/admin(\\/|$)/.test(path)) return 'admin';
      if (/\\/tracker(\\/|$)/.test(path)) return 'tracker';
      if (/\\/council(\\/|$)/.test(path)) return 'council';
      if (/\\/news-desk(\\/|$)/.test(path)) return 'news';
      return '';
    }

    function detectRole() {
      var pathRole = roleFromPath(window.location.pathname || '');
      if (pathRole) return pathRole;
      var links = Array.prototype.slice.call(document.querySelectorAll('a[href]'));
      for (var i = 0; i < links.length; i += 1) {
        var href = links[i].getAttribute('href') || '';
        var path = href;
        try {
          path = new URL(href, window.location.origin).pathname;
        } catch (error) {}
        var linkRole = roleFromPath(path);
        if (linkRole) return linkRole;
      }
      return '';
    }

    function reportAuthStatus() {
      if (!window.ReactNativeWebView || !document.body) return;
      var authenticated = !!document.querySelector('form.nav-inline-form[action*="/logout"]');
      var hasLoginLink = !!document.querySelector('a[href*="/login"]');
      window.ReactNativeWebView.postMessage(JSON.stringify({
        type: 'authStatus',
        authenticated: authenticated,
        hasLoginLink: hasLoginLink,
        path: window.location.pathname,
        role: authenticated ? detectRole() : ''
      }));
    }

    function applyMobileChrome() {
      if (!document.head) {
        setTimeout(applyMobileChrome, 30);
        return;
      }
      var existing = document.getElementById('arlington-mobile-webview-style');
      if (!existing) {
        var style = document.createElement('style');
        style.id = 'arlington-mobile-webview-style';
        style.textContent = [
          '.site-header, .site-footer, .skip-link { display: none !important; }',
          'body { min-height: 100vh !important; }',
          '.main { max-width: 100% !important; padding: 1rem 0.85rem 2rem !important; }',
          '.main-wide { max-width: 100% !important; }',
          '.page-header { margin-top: 0 !important; }',
          '.alerts { margin-top: 0 !important; }'
        ].join('\\n');
        document.head.appendChild(style);
      }
      reportAuthStatus();
      setTimeout(reportAuthStatus, 250);
      setTimeout(reportAuthStatus, 800);
    }
    applyMobileChrome();
  })();
  true;
`;

const logoutScript = `
  (function () {
    setTimeout(function () {
      if (window.__arlingtonLogoutStarted) return;
      var form = document.querySelector('form.nav-inline-form[action*="/logout"]');
      if (form) {
        window.__arlingtonLogoutStarted = true;
        fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          credentials: 'include',
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
          .then(function (response) {
            return response.json().catch(function () {
              return { ok: response.ok };
            });
          })
          .then(function (payload) {
            if (window.ReactNativeWebView) {
              window.ReactNativeWebView.postMessage(JSON.stringify({
                type: 'logoutResult',
                ok: !!payload.ok,
                message: payload.message || ''
              }));
            }
          })
          .catch(function (error) {
            window.__arlingtonLogoutStarted = false;
            if (window.ReactNativeWebView) {
              window.ReactNativeWebView.postMessage(JSON.stringify({
                type: 'logoutResult',
                ok: false,
                message: error && error.message ? error.message : ''
              }));
            }
          });
      } else if (window.ReactNativeWebView) {
        window.ReactNativeWebView.postMessage(JSON.stringify({
          type: 'authStatus',
          authenticated: false,
          path: window.location.pathname,
          role: ''
        }));
      }
    }, 250);
  })();
  true;
`;

function AuthProbe({ locale, apiBaseUrl, onAuthChange }) {
  const handleProbeMessage = (event) => {
    try {
      const payload = JSON.parse(event.nativeEvent.data);
      if (payload.type === "authStatus") {
        onAuthChange(Boolean(payload.authenticated), payload.path || "", payload.role || "");
      }
    } catch {
      // Ignore unexpected page messages.
    }
  };

  return (
    <View pointerEvents="none" style={styles.authProbe}>
      <WebView
        source={{ uri: `${apiBaseUrl}/${locale}/dashboard` }}
        originWhitelist={["*"]}
        sharedCookiesEnabled
        thirdPartyCookiesEnabled
        injectedJavaScriptBeforeContentLoaded={webChromeScript}
        injectedJavaScript={webChromeScript}
        onMessage={handleProbeMessage}
      />
    </View>
  );
}

function WebScreen({ locale, page, close, dir, onAuthChange }) {
  const webRef = useRef(null);
  const [canGoBack, setCanGoBack] = useState(false);
  const [webLoading, setWebLoading] = useState(true);
  const [webError, setWebError] = useState("");

  const goBackOrClose = () => {
    if (canGoBack && webRef.current) webRef.current.goBack();
    else close();
  };

  const handleWebMessage = (event) => {
    try {
      const payload = JSON.parse(event.nativeEvent.data);
      if (payload.type === "authStatus") {
        onAuthChange(Boolean(payload.authenticated), payload.path || "", payload.role || "");
      } else if (payload.type === "logoutResult") {
        if (payload.ok) {
          onAuthChange(false, "");
        } else {
          setWebError(payload.message || t(locale, "logoutFailed"));
        }
      }
    } catch {
      // Ignore messages from pages that are not part of the council site.
    }
  };

  return (
    <View style={styles.webScreen}>
      <View style={[styles.webHeader, dir.row]}>
        <Pressable accessibilityRole="button" style={styles.webHeaderButton} onPress={goBackOrClose}>
          <Text style={styles.webHeaderButtonText} allowFontScaling={false}>{canGoBack ? "<" : "X"}</Text>
        </Pressable>
        <View style={[styles.webTitleBlock, dir.align]}>
          <Text style={[styles.webTitle, dir.text]} numberOfLines={1}>{page.title || t(locale, "websitePage")}</Text>
          <Text style={[styles.webUrl, dir.text]} numberOfLines={1}>{page.url}</Text>
        </View>
      </View>
      <View style={styles.webBody}>
        {webError ? (
          <View style={styles.webErrorPanel}>
            <Text style={[styles.cardTitle, dir.text]}>{t(locale, "webLoadError")}</Text>
            <Text style={[styles.muted, dir.text]}>{webError}</Text>
          </View>
        ) : null}
        <WebView
          ref={webRef}
          source={{ uri: page.url }}
          style={styles.webView}
          originWhitelist={["*"]}
          sharedCookiesEnabled
          thirdPartyCookiesEnabled
          startInLoadingState
          injectedJavaScriptBeforeContentLoaded={webChromeScript}
          injectedJavaScript={page.action === "logout" ? `${webChromeScript}\n${logoutScript}` : webChromeScript}
          onLoadStart={() => {
            setWebLoading(true);
            setWebError("");
          }}
          onLoadEnd={() => setWebLoading(false)}
          onNavigationStateChange={(state) => {
            setCanGoBack(state.canGoBack);
            if (webRef.current) {
              webRef.current.injectJavaScript(page.action === "logout" ? `${webChromeScript}\n${logoutScript}` : webChromeScript);
            }
          }}
          onMessage={handleWebMessage}
          onError={(event) => {
            setWebLoading(false);
            setWebError(event.nativeEvent.description || t(locale, "webLoadError"));
          }}
        />
        {webLoading ? (
          <View style={styles.webLoading}>
            <ActivityIndicator color={palette.green} size="large" />
            <Text style={[styles.muted, dir.text]}>{t(locale, "loading")}</Text>
          </View>
        ) : null}
      </View>
    </View>
  );
}

function ErrorPanel({ locale, message, onRetry, dir }) {
  return (
    <View style={styles.errorPanel}>
      <Text style={[styles.cardTitle, dir.text]}>{t(locale, "errorTitle")}</Text>
      <Text style={[styles.muted, dir.text]}>{message}</Text>
      <Pressable style={styles.primaryButton} onPress={onRetry}>
        <Text style={styles.primaryButtonText}>{t(locale, "retry")}</Text>
      </Pressable>
    </View>
  );
}

function HomeScreen({ locale, data, dir, openWeb }) {
  return (
    <View style={styles.stack}>
      <View style={styles.heroCard}>
        <View style={styles.heroAccent} />
        <View style={styles.heroCopyBlock}>
          <Text style={[styles.eyebrow, dir.text]}>{t(locale, "cityWork")}</Text>
          <Text style={[styles.heroTitle, dir.text]}>{t(locale, "heroTitle")}</Text>
        </View>
        <View style={[styles.heroStatusRow, dir.row]}>
          <Text style={[styles.heroStatusText, dir.text]}>{t(locale, "liveNumbers")}</Text>
          <Text style={styles.heroStatusBadge}>{data.stats?.active_projects || 0}</Text>
        </View>
        <StatGrid locale={locale} stats={data.stats} dir={dir} />
      </View>
      <PostSection locale={locale} title={t(locale, "announcements")} posts={data.announcements} dir={dir} />
      <ProjectMiniSection locale={locale} projects={data.recentProjects} dir={dir} />
      <PostSection locale={locale} title={t(locale, "news")} posts={data.news} dir={dir} />
      <UsefulSites locale={locale} sites={data.usefulSites.slice(0, 6)} dir={dir} openWeb={openWeb} />
    </View>
  );
}

function StatGrid({ locale, stats, dir }) {
  const items = [
    [t(locale, "projects"), stats.projects || 0],
    [t(locale, "votes"), stats.open_votes || 0],
    [t(locale, "volunteers"), stats.volunteers || 0],
    [t(locale, "tracker"), stats.trackers || 0]
  ];
  return (
    <View style={styles.statGrid}>
      {items.map(([label, value]) => (
        <View key={label} style={styles.statBox}>
          <Text style={[styles.statValue, dir.text]}>{value}</Text>
          <Text style={[styles.statLabel, dir.text]}>{label}</Text>
        </View>
      ))}
    </View>
  );
}

function PostSection({ locale, title, posts, dir }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.sectionTitle, dir.text]}>{title}</Text>
      {posts.length ? posts.map((post) => <PostCard key={post.id} post={post} dir={dir} />) : <Empty locale={locale} dir={dir} />}
    </View>
  );
}

function PostCard({ post, dir }) {
  return (
    <View style={styles.card}>
      {post.image_url ? <Image source={{ uri: post.image_url }} style={styles.postImage} /> : null}
      <Text style={[styles.cardTitle, dir.text]}>{post.title}</Text>
      <Text style={[styles.muted, dir.text]}>{post.summary || post.body_text || post.body}</Text>
    </View>
  );
}

function ProjectMiniSection({ locale, projects, dir }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.sectionTitle, dir.text]}>{t(locale, "recentProjects")}</Text>
      {projects.length ? projects.slice(0, 3).map((project) => <ProjectCard key={project.id} locale={locale} project={project} dir={dir} compact />) : <Empty locale={locale} dir={dir} />}
    </View>
  );
}

function ProjectsScreen(props) {
  const { locale, projects, dir } = props;
  return (
    <View style={styles.section}>
      <Text style={[styles.screenTitle, dir.text]}>{t(locale, "projects")}</Text>
      {projects.length ? projects.map((project) => <ProjectCard key={project.id} {...props} project={project} />) : <Empty locale={locale} dir={dir} />}
    </View>
  );
}

function ProjectCard({
  locale,
  project,
  dir,
  compact = false,
  volunteerProjectId,
  setVolunteerProjectId,
  volunteerForm,
  setVolunteerForm,
  onVolunteer,
  openWeb
}) {
  const isVolunteering = volunteerProjectId === project.id;
  return (
    <View style={styles.card}>
      <View style={[styles.cardTop, dir.row]}>
        <Text style={[styles.cardTitle, dir.text]}>{project.title}</Text>
        <Text style={styles.statusPill}>{statusLabel(locale, project.status)}</Text>
      </View>
      <Text style={[styles.muted, dir.text]} numberOfLines={compact ? 2 : 5}>{project.description}</Text>
      <ProgressBar value={project.progress} />
      <View style={styles.metaGrid}>
        <Meta locale={locale} label={t(locale, "tracker")} value={project.tracker || t(locale, "notScheduled")} dir={dir} />
        <Meta locale={locale} label={t(locale, "volunteers")} value={project.volunteer_count} dir={dir} />
        <Meta locale={locale} label={t(locale, "start")} value={formatDate(project.start_date, locale)} dir={dir} />
        <Meta locale={locale} label={t(locale, "deadline")} value={formatDate(project.voting_deadline, locale)} dir={dir} />
      </View>
      {!compact ? (
        <View style={[styles.actionRow, dir.row]}>
          <Pressable style={styles.secondaryButton} onPress={() => openWeb(project.url, project.title)}>
            <Text style={styles.secondaryButtonText}>{t(locale, "openWebsite")}</Text>
          </Pressable>
          <Pressable style={styles.primaryButton} onPress={() => setVolunteerProjectId(isVolunteering ? null : project.id)}>
            <Text style={styles.primaryButtonText}>{t(locale, "volunteer")}</Text>
          </Pressable>
        </View>
      ) : null}
      {isVolunteering ? (
        <View style={styles.formBlock}>
          <Input locale={locale} value={volunteerForm.name} onChangeText={(name) => setVolunteerForm({ ...volunteerForm, name })} placeholder={t(locale, "volunteerName")} />
          <Input locale={locale} value={volunteerForm.additional_info} onChangeText={(additional_info) => setVolunteerForm({ ...volunteerForm, additional_info })} placeholder={t(locale, "volunteerNote")} multiline />
          <Pressable style={styles.primaryButton} onPress={() => onVolunteer(project.id)}>
            <Text style={styles.primaryButtonText}>{t(locale, "sendVolunteer")}</Text>
          </Pressable>
        </View>
      ) : null}
    </View>
  );
}

function DonationsScreen({ locale, campaigns, dir, pledgeCampaignId, setPledgeCampaignId, pledgeForm, setPledgeForm, onPledge, openWeb }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.screenTitle, dir.text]}>{t(locale, "campaigns")}</Text>
      {campaigns.length ? campaigns.map((campaign) => (
        <DonationCard
          key={campaign.id}
          locale={locale}
          campaign={campaign}
          dir={dir}
          pledgeCampaignId={pledgeCampaignId}
          setPledgeCampaignId={setPledgeCampaignId}
          pledgeForm={pledgeForm}
          setPledgeForm={setPledgeForm}
          onPledge={onPledge}
          openWeb={openWeb}
        />
      )) : <Empty locale={locale} dir={dir} />}
    </View>
  );
}

function DonationCard({ locale, campaign, dir, pledgeCampaignId, setPledgeCampaignId, pledgeForm, setPledgeForm, onPledge, openWeb }) {
  const isPledging = pledgeCampaignId === campaign.id;
  return (
    <View style={styles.card}>
      <Text style={[styles.cardTitle, dir.text]}>{campaign.title}</Text>
      <Text style={[styles.muted, dir.text]}>{campaign.description}</Text>
      <ProgressBar value={campaign.progress} />
      <View style={styles.metaGrid}>
        <Meta locale={locale} label={t(locale, "confirmed")} value={money(campaign.confirmed_total, campaign.currency)} dir={dir} />
        <Meta locale={locale} label={t(locale, "pledged")} value={money(campaign.pledged_total, campaign.currency)} dir={dir} />
        <Meta locale={locale} label={t(locale, "goal")} value={money(campaign.goal_amount, campaign.currency)} dir={dir} />
        <Meta locale={locale} label={t(locale, "progress")} value={`${campaign.progress}%`} dir={dir} />
      </View>
      {campaign.groups?.length ? (
        <View style={styles.groupRail}>
          {campaign.groups.slice(0, 4).map((group) => (
            <View key={group.id} style={styles.groupChip}>
              <Text style={styles.groupName}>{group.name}</Text>
              <Text style={styles.groupAmount}>{money(group.confirmed_total, campaign.currency)}</Text>
            </View>
          ))}
        </View>
      ) : null}
      <View style={[styles.actionRow, dir.row]}>
        <Pressable style={styles.secondaryButton} onPress={() => openWeb(campaign.url, campaign.title)}>
          <Text style={styles.secondaryButtonText}>{t(locale, "openWebsite")}</Text>
        </Pressable>
        <Pressable style={styles.primaryButton} onPress={() => setPledgeCampaignId(isPledging ? null : campaign.id)}>
          <Text style={styles.primaryButtonText}>{t(locale, "give")}</Text>
        </Pressable>
      </View>
      {isPledging ? (
        <View style={styles.formBlock}>
          <Input locale={locale} value={pledgeForm.donor_name} onChangeText={(donor_name) => setPledgeForm({ ...pledgeForm, donor_name })} placeholder={t(locale, "donorName")} />
          <Input locale={locale} value={pledgeForm.amount} onChangeText={(amount) => setPledgeForm({ ...pledgeForm, amount })} placeholder={t(locale, "amount")} keyboardType="decimal-pad" />
          <Input locale={locale} value={pledgeForm.new_group_name} onChangeText={(new_group_name) => setPledgeForm({ ...pledgeForm, new_group_name })} placeholder={t(locale, "groupName")} />
          <Input locale={locale} value={pledgeForm.message} onChangeText={(message) => setPledgeForm({ ...pledgeForm, message })} placeholder={t(locale, "message")} multiline />
          <Pressable style={[styles.toggleRow, dir.row]} onPress={() => setPledgeForm({ ...pledgeForm, display_name: !pledgeForm.display_name })}>
            <View style={[styles.checkbox, pledgeForm.display_name && styles.checkboxOn]} />
            <Text style={[styles.toggleText, dir.text]}>{t(locale, "displayName")}</Text>
          </Pressable>
          <Text style={[styles.smallText, dir.text]}>{t(locale, "paymentNote")}</Text>
          <Pressable style={styles.primaryButton} onPress={() => onPledge(campaign.id)}>
            <Text style={styles.primaryButtonText}>{t(locale, "submitPledge")}</Text>
          </Pressable>
        </View>
      ) : null}
    </View>
  );
}

function ProposalsScreen({ locale, proposals, dir, openWeb }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.screenTitle, dir.text]}>{t(locale, "publicProposals")}</Text>
      {proposals.length ? proposals.map((proposal) => (
        <View key={proposal.id} style={styles.card}>
          <View style={[styles.cardTop, dir.row]}>
            <Text style={[styles.cardTitle, dir.text]}>{proposal.title}</Text>
            <Text style={styles.statusPill}>{proposal.is_open_for_voting ? t(locale, "openForVoting") : t(locale, "closed")}</Text>
          </View>
          <Text style={[styles.muted, dir.text]}>{proposal.summary || proposal.body}</Text>
          <View style={styles.metaGrid}>
            <Meta locale={locale} label={t(locale, "yes")} value={proposal.vote_counts?.Yes || 0} dir={dir} />
            <Meta locale={locale} label={t(locale, "no")} value={proposal.vote_counts?.No || 0} dir={dir} />
            <Meta locale={locale} label={t(locale, "abstain")} value={proposal.vote_counts?.Abstain || 0} dir={dir} />
            <Meta locale={locale} label={t(locale, "deadline")} value={formatDate(proposal.voting_deadline, locale)} dir={dir} />
          </View>
          <Pressable style={styles.secondaryButton} onPress={() => openWeb(proposal.url, proposal.title)}>
            <Text style={styles.secondaryButtonText}>{t(locale, "openWebsite")}</Text>
          </Pressable>
        </View>
      )) : <Empty locale={locale} dir={dir} />}
    </View>
  );
}

function SuggestionsScreen({ locale, projects, suggestion, setSuggestion, onSubmit, dir }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.screenTitle, dir.text]}>{t(locale, "suggestionTitle")}</Text>
      <View style={styles.card}>
        <View style={[styles.segment, dir.row]}>
          <Pressable
            style={[styles.segmentButton, suggestion.target_type === "council" && styles.segmentButtonActive]}
            onPress={() => setSuggestion({ ...suggestion, target_type: "council" })}
          >
            <Text style={[styles.segmentText, suggestion.target_type === "council" && styles.segmentTextActive]}>{t(locale, "targetCouncil")}</Text>
          </Pressable>
          <Pressable
            style={[styles.segmentButton, suggestion.target_type === "project_tracker" && styles.segmentButtonActive]}
            onPress={() => setSuggestion({ ...suggestion, target_type: "project_tracker", project_id: suggestion.project_id || projects[0]?.id || "" })}
          >
            <Text style={[styles.segmentText, suggestion.target_type === "project_tracker" && styles.segmentTextActive]}>{t(locale, "targetProject")}</Text>
          </Pressable>
        </View>
        {suggestion.target_type === "project_tracker" ? (
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.projectPicker}>
            {projects.map((project) => (
              <Pressable
                key={project.id}
                style={[styles.projectPick, Number(suggestion.project_id) === project.id && styles.projectPickActive]}
                onPress={() => setSuggestion({ ...suggestion, project_id: project.id })}
              >
                <Text style={[styles.projectPickText, Number(suggestion.project_id) === project.id && styles.projectPickTextActive]}>{project.title}</Text>
              </Pressable>
            ))}
          </ScrollView>
        ) : null}
        <Input locale={locale} value={suggestion.name} onChangeText={(name) => setSuggestion({ ...suggestion, name })} placeholder={t(locale, "nameOptional")} />
        <Input locale={locale} value={suggestion.contact} onChangeText={(contact) => setSuggestion({ ...suggestion, contact })} placeholder={t(locale, "contactOptional")} />
        <Input locale={locale} value={suggestion.title} onChangeText={(title) => setSuggestion({ ...suggestion, title })} placeholder={t(locale, "title")} />
        <Input locale={locale} value={suggestion.body} onChangeText={(body) => setSuggestion({ ...suggestion, body })} placeholder={t(locale, "details")} multiline />
        <Pressable style={styles.primaryButton} onPress={onSubmit}>
          <Text style={styles.primaryButtonText}>{t(locale, "submitSuggestion")}</Text>
        </Pressable>
      </View>
    </View>
  );
}

function MoreScreen({ locale, sites, openWeb, dir }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.screenTitle, dir.text]}>{t(locale, "more")}</Text>
      <UsefulSites locale={locale} sites={sites} dir={dir} openWeb={openWeb} />
    </View>
  );
}

function UsefulSites({ locale, sites, dir, openWeb }) {
  return (
    <View style={styles.section}>
      <Text style={[styles.sectionTitle, dir.text]}>{t(locale, "usefulSites")}</Text>
      {sites.length ? sites.map((site, index) => (
        <Pressable key={`${site.title}-${index}`} style={[styles.siteCard, dir.row]} onPress={() => openWeb(site.url, site.title)}>
          <View style={styles.globeMark}><Text style={styles.globeText}>G</Text></View>
          <View style={[styles.siteText, dir.align]}>
            <Text style={[styles.cardTitle, dir.text]}>{site.title}</Text>
            <Text style={[styles.muted, dir.text]}>{site.description}</Text>
          </View>
        </Pressable>
      )) : <Empty locale={locale} dir={dir} />}
    </View>
  );
}

function Meta({ label, value, dir }) {
  return (
    <View style={styles.metaBox}>
      <Text style={[styles.metaLabel, dir.text]}>{label}</Text>
      <Text style={[styles.metaValue, dir.text]}>{value}</Text>
    </View>
  );
}

function ProgressBar({ value }) {
  const width = `${Math.max(0, Math.min(100, Number(value || 0)))}%`;
  return (
    <View style={styles.progressWrap}>
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width }]} />
      </View>
      <Text style={styles.progressText}>{Math.round(Number(value || 0))}%</Text>
    </View>
  );
}

function Input({ locale, style, ...props }) {
  const isRtl = false;
  return (
    <TextInput
      placeholderTextColor="#8a9a92"
      style={[styles.input, isRtl ? styles.textRtl : styles.textLtr, props.multiline && styles.inputTall, style]}
      textAlign={isRtl ? "right" : "left"}
      {...props}
    />
  );
}

function Empty({ locale, dir }) {
  return <Text style={[styles.empty, dir.text]}>{t(locale, "noItems")}</Text>;
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: palette.greenDeep
  },
  appFrame: {
    flex: 1,
    backgroundColor: "#edf5fb"
  },
  contentFrame: {
    flex: 1
  },
  authProbe: {
    position: "absolute",
    width: 1,
    height: 1,
    left: -10,
    top: -10,
    opacity: 0,
    overflow: "hidden"
  },
  header: {
    backgroundColor: palette.greenDeep,
    paddingTop: Platform.OS === "android" ? (StatusBar.currentHeight || 24) + 8 : 10,
    paddingHorizontal: 14,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: "rgba(245,128,37,0.55)",
    zIndex: 4
  },
  headerTop: {
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
    minHeight: 48
  },
  brandCluster: {
    flex: 1,
    alignItems: "center",
    gap: 9,
    minWidth: 0
  },
  brandCopy: {
    flex: 1,
    minWidth: 0
  },
  logoMark: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: palette.white,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.5)",
    overflow: "hidden"
  },
  logoImage: {
    width: 38,
    height: 38
  },
  brandTitle: {
    color: palette.white,
    fontWeight: "900",
    fontSize: 17,
    lineHeight: 20
  },
  brandSub: {
    color: "rgba(255,255,255,0.82)",
    fontWeight: "800",
    fontSize: 11,
    marginTop: 1
  },
  langButton: {
    width: 48,
    height: 42,
    borderRadius: 12,
    backgroundColor: palette.black,
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)"
  },
  langButtonText: {
    color: palette.white,
    fontWeight: "900",
    fontSize: 14
  },
  tabWrap: {
    backgroundColor: "#fdfbf7",
    borderTopWidth: 1,
    borderTopColor: palette.line,
    paddingHorizontal: 10,
    paddingTop: 10,
    paddingBottom: Platform.OS === "android" ? 10 : 18,
    ...compactShadow
  },
  tabScroller: {
    flexDirection: "row",
    gap: 8
  },
  tab: {
    flex: 1,
    minHeight: 54,
    paddingHorizontal: 4,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#ffffff",
    borderWidth: 1,
    borderColor: palette.line
  },
  tabActive: {
    backgroundColor: palette.greenDeep,
    borderColor: palette.greenDeep
  },
  tabText: {
    color: palette.muted,
    fontWeight: "900",
    fontSize: 11
  },
  tabTextActive: {
    color: palette.white
  },
  sheetRoot: {
    flex: 1,
    justifyContent: "flex-end"
  },
  sheetBackdrop: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(8, 16, 12, 0.46)"
  },
  sheetPanel: {
    height: "86%",
    backgroundColor: "#fdfbf7",
    borderTopLeftRadius: 26,
    borderTopRightRadius: 26,
    paddingHorizontal: 14,
    paddingTop: 10,
    borderWidth: 1,
    borderColor: palette.line
  },
  sheetHeader: {
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: palette.line
  },
  sheetHandleBlock: {
    flex: 1,
    gap: 4
  },
  sheetHandle: {
    width: 46,
    height: 5,
    borderRadius: 99,
    backgroundColor: "#c7d4cd",
    marginBottom: 7
  },
  sheetTitle: {
    color: palette.ink,
    fontWeight: "900",
    fontSize: 26,
    lineHeight: 31
  },
  sheetSubtitle: {
    color: palette.muted,
    fontWeight: "700",
    fontSize: 14,
    lineHeight: 20
  },
  sheetClose: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: palette.black,
    alignItems: "center",
    justifyContent: "center"
  },
  sheetCloseText: {
    color: palette.white,
    fontWeight: "900",
    fontSize: 14
  },
  sheetScroll: {
    paddingTop: 14,
    paddingBottom: 28,
    gap: 10
  },
  optionCard: {
    alignItems: "center",
    gap: 12,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: palette.line,
    backgroundColor: palette.card,
    padding: 14,
    ...compactShadow
  },
  optionIcon: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: palette.greenDeep,
    alignItems: "center",
    justifyContent: "center"
  },
  optionIconText: {
    color: palette.white,
    fontWeight: "900",
    fontSize: 15
  },
  optionTextBlock: {
    flex: 1,
    minWidth: 0,
    gap: 3
  },
  optionTitle: {
    color: palette.ink,
    fontWeight: "900",
    fontSize: 17,
    lineHeight: 22
  },
  optionBody: {
    color: palette.muted,
    fontWeight: "700",
    fontSize: 13,
    lineHeight: 19
  },
  webScreen: {
    flex: 1,
    backgroundColor: palette.bg
  },
  webHeader: {
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: palette.line,
    backgroundColor: palette.card
  },
  webHeaderButton: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: palette.black,
    alignItems: "center",
    justifyContent: "center"
  },
  webHeaderButtonText: {
    color: palette.white,
    fontWeight: "900",
    fontSize: 14
  },
  webTitleBlock: {
    flex: 1,
    minWidth: 0
  },
  webTitle: {
    color: palette.ink,
    fontWeight: "900",
    fontSize: 16,
    lineHeight: 20
  },
  webUrl: {
    color: palette.muted,
    fontWeight: "700",
    fontSize: 11,
    lineHeight: 15,
    marginTop: 1
  },
  webBody: {
    flex: 1,
    backgroundColor: palette.white
  },
  webView: {
    flex: 1,
    backgroundColor: palette.white
  },
  webLoading: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    backgroundColor: "rgba(255,255,255,0.88)"
  },
  webErrorPanel: {
    position: "absolute",
    left: 14,
    right: 14,
    top: 14,
    zIndex: 3,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#f0c2c8",
    backgroundColor: "#fff4f5",
    padding: 14,
    gap: 8
  },
  notice: {
    margin: 12,
    marginBottom: 0,
    padding: 12,
    borderRadius: 8,
    backgroundColor: palette.greenSoft,
    color: palette.greenDeep,
    fontWeight: "800"
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 18
  },
  loadingPanel: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    gap: 12
  },
  stack: {
    gap: 14
  },
  heroCard: {
    backgroundColor: palette.greenDeep,
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: "#0e5f98",
    overflow: "hidden",
    ...shadow
  },
  heroAccent: {
    position: "absolute",
    right: -30,
    top: -24,
    width: 130,
    height: 130,
    borderRadius: 70,
    backgroundColor: "rgba(245,128,37,0.22)"
  },
  heroCopyBlock: {
    maxWidth: "96%"
  },
  heroStatusRow: {
    alignItems: "center",
    justifyContent: "space-between",
    marginTop: 18,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: "rgba(255,255,255,0.18)"
  },
  heroStatusText: {
    color: "#dcecf8",
    fontWeight: "900",
    fontSize: 13,
    textTransform: "uppercase"
  },
  heroStatusBadge: {
    minWidth: 38,
    textAlign: "center",
    overflow: "hidden",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
    color: palette.greenDeep,
    backgroundColor: palette.red,
    fontWeight: "900"
  },
  eyebrow: {
    color: palette.red,
    fontWeight: "900",
    textTransform: "uppercase",
    fontSize: 12,
    marginBottom: 8
  },
  heroTitle: {
    color: palette.white,
    fontSize: 25,
    lineHeight: 31,
    fontWeight: "900"
  },
  statGrid: {
    marginTop: 18,
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  statBox: {
    flexGrow: 1,
    flexBasis: "44%",
    borderRadius: 16,
    padding: 14,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.22)"
  },
  statValue: {
    color: palette.white,
    fontWeight: "900",
    fontSize: 28
  },
  statLabel: {
    color: "#dcecf8",
    fontWeight: "800",
    marginTop: 2
  },
  section: {
    gap: 12
  },
  screenTitle: {
    color: palette.black,
    fontWeight: "900",
    fontSize: 30,
    lineHeight: 34
  },
  sectionTitle: {
    color: palette.greenDeep,
    fontWeight: "900",
    fontSize: 20
  },
  card: {
    backgroundColor: palette.card,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: palette.line,
    gap: 11,
    ...compactShadow
  },
  errorPanel: {
    backgroundColor: "#fff4f5",
    borderWidth: 1,
    borderColor: "#f0c2c8",
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    gap: 10
  },
  cardTop: {
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 8
  },
  cardTitle: {
    color: palette.ink,
    fontWeight: "900",
    fontSize: 17,
    lineHeight: 22
  },
  muted: {
    color: palette.muted,
    fontSize: 15,
    lineHeight: 22
  },
  smallText: {
    color: palette.muted,
    fontSize: 13,
    lineHeight: 19
  },
  statusPill: {
    overflow: "hidden",
    borderRadius: 999,
    paddingHorizontal: 10,
    paddingVertical: 5,
    backgroundColor: "#fff1e6",
    color: "#a74b00",
    fontWeight: "900",
    fontSize: 12
  },
  progressWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10
  },
  progressTrack: {
    flex: 1,
    height: 10,
    borderRadius: 99,
    overflow: "hidden",
    backgroundColor: "#dce6df"
  },
  progressFill: {
    height: "100%",
    borderRadius: 99,
    backgroundColor: palette.red
  },
  progressText: {
    color: palette.greenDeep,
    fontWeight: "900",
    fontSize: 12
  },
  metaGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  metaBox: {
    flexGrow: 1,
    flexBasis: "45%",
    padding: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.line,
    backgroundColor: "#f7fbff"
  },
  metaLabel: {
    color: palette.muted,
    fontWeight: "800",
    fontSize: 12
  },
  metaValue: {
    color: palette.ink,
    fontWeight: "900",
    fontSize: 15,
    marginTop: 2
  },
  actionRow: {
    alignItems: "center",
    gap: 9,
    flexWrap: "wrap"
  },
  primaryButton: {
    minHeight: 46,
    borderRadius: 14,
    backgroundColor: palette.greenDeep,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center"
  },
  primaryButtonText: {
    color: palette.white,
    fontWeight: "900"
  },
  secondaryButton: {
    minHeight: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.line,
    backgroundColor: palette.white,
    paddingHorizontal: 16,
    alignItems: "center",
    justifyContent: "center"
  },
  secondaryButtonText: {
    color: palette.greenDeep,
    fontWeight: "900"
  },
  formBlock: {
    gap: 10,
    padding: 12,
    borderRadius: 16,
    backgroundColor: "#f7fbff",
    borderWidth: 1,
    borderColor: palette.line
  },
  input: {
    minHeight: 46,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: palette.line,
    backgroundColor: palette.white,
    color: palette.ink,
    paddingHorizontal: 12,
    fontSize: 15,
    fontWeight: "700"
  },
  inputTall: {
    minHeight: 92,
    paddingTop: 12,
    textAlignVertical: "top"
  },
  groupRail: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8
  },
  groupChip: {
    borderRadius: 8,
    padding: 10,
    backgroundColor: palette.soft,
    borderWidth: 1,
    borderColor: palette.line
  },
  groupName: {
    color: palette.greenDeep,
    fontWeight: "900"
  },
  groupAmount: {
    color: palette.muted,
    fontWeight: "800",
    marginTop: 2
  },
  toggleRow: {
    alignItems: "center",
    gap: 9
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 5,
    borderWidth: 2,
    borderColor: palette.green
  },
  checkboxOn: {
    backgroundColor: palette.green
  },
  toggleText: {
    color: palette.ink,
    fontWeight: "800"
  },
  segment: {
    gap: 8
  },
  segmentButton: {
    flex: 1,
    minHeight: 44,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: palette.line,
    alignItems: "center",
    justifyContent: "center"
  },
  segmentButtonActive: {
    backgroundColor: palette.green,
    borderColor: palette.green
  },
  segmentText: {
    color: palette.greenDeep,
    fontWeight: "900"
  },
  segmentTextActive: {
    color: palette.white
  },
  projectPicker: {
    gap: 8
  },
  projectPick: {
    paddingHorizontal: 12,
    minHeight: 38,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: palette.line,
    alignItems: "center",
    justifyContent: "center"
  },
  projectPickActive: {
    backgroundColor: palette.greenSoft,
    borderColor: palette.green
  },
  projectPickText: {
    color: palette.muted,
    fontWeight: "800"
  },
  projectPickTextActive: {
    color: palette.greenDeep
  },
  postImage: {
    width: "100%",
    height: 170,
    borderRadius: 8,
    backgroundColor: palette.soft
  },
  siteCard: {
    alignItems: "center",
    gap: 12,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: palette.line,
    backgroundColor: palette.card,
    padding: 14,
    ...compactShadow
  },
  globeMark: {
    width: 42,
    height: 42,
    borderRadius: 24,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: palette.greenDeep
  },
  globeText: {
    color: palette.white,
    fontWeight: "900"
  },
  siteText: {
    flex: 1,
    gap: 2
  },
  empty: {
    color: palette.muted,
    padding: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: palette.line,
    backgroundColor: palette.soft,
    fontWeight: "700"
  },
  row: {
    flexDirection: "row"
  },
  rowReverse: {
    flexDirection: "row-reverse"
  },
  alignStart: {
    alignItems: "flex-start"
  },
  alignEnd: {
    alignItems: "flex-end"
  },
  textLtr: {
    textAlign: "left",
    writingDirection: "ltr"
  },
  textRtl: {
    textAlign: "right",
    writingDirection: "rtl"
  }
});
