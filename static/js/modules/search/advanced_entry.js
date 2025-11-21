/**
 * Advanced Search Entry Point
 * Consolidates all initialization logic for the advanced search page.
 */

import { initTabs } from "./tabs.js";
import { initStatsTabAdvanced, cleanupStats } from "../stats/initStatsTabAdvanced.js";
import { initRegionalToggle } from "./regional-toggle.js";

// Import modules that have side-effects (auto-init) or are dependencies
import "./config.js";
import "./filters.js";
import "./patternBuilder.js";
import "./searchUI.js";
import "../advanced/initTable.js";
import "../stats/renderBar.js";
import "./token-tab.js";
import "../advanced/index.js"; // This one auto-inits initAdvancedApp

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initStatsTabAdvanced();
    initRegionalToggle();
});

window.addEventListener('beforeunload', cleanupStats);
