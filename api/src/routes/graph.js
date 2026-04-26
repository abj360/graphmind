#!/usr/bin/env node
/**
 * graph.js --- graph read endpoints backing the viewer
 *  *
 *  * Contains:
 *  *   imports + router factory
 */

import { Router } from "express";

import { runQuery } from "../neo4jClient.js";
