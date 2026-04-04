#!/usr/bin/env node
/**
 * MetricsDashboard.jsx --- dashboard panel showing node/edge dedup metrics
 *  *
 *  * Contains:
 */

import { useEffect, useState } from "react";

import { fetchDedupMetrics } from "../apiClient.js";
