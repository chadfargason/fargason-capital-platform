/**
 * Portfolio Calculation API Route - SIMPLIFIED VERSION
 * 
 * This version is MUCH cleaner because it only handles:
 * - HTTP concerns (CORS, request/response)
 * - Orchestration (calling the right modules)
 * - Error handling at the HTTP level
 * 
 * All the heavy lifting is done by separate modules.
 */

import { NextResponse } from 'next/server';
import { writeFile } from 'fs/promises';
import { join } from 'path';
import { getDataService } from '@/lib/portfolioDataService';
import {
  calculatePortfolio,
  generateCSV,
  type PortfolioConfig
} from '@/lib/portfolioCalculator';

// ============================================================================
// Type Definitions
// ============================================================================

interface CalculateRequest {
  assets: string[];
  weights: number[];
  startDate: string;
  endDate: string;
  rebalanceMonths?: number;
  generateCSV?: boolean;
  riskFreeRate?: number; // Allow custom risk-free rate
}

// ============================================================================
// Helper Functions
// ============================================================================

function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

async function saveCSVLog(csv: string): Promise<string> {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  const filename = `Returns_Log_${timestamp}.csv`;
  const filepath = join('/tmp', filename);
  
  await writeFile(filepath, csv, 'utf-8');
  console.log(`✓ CSV log saved to: ${filepath} (${(csv.length / 1024).toFixed(1)} KB)`);
  
  return filename;
}

// ============================================================================
// API Route Handlers
// ============================================================================

export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders() });
}

export async function POST(request: Request) {
  const startTime = Date.now();
  
  try {
    // Parse request
    const body: CalculateRequest = await request.json();
    console.log(`[API] Request: ${body.assets.length} assets, ${body.startDate} to ${body.endDate}`);
    
    // Get data service (will check env vars)
    const dataService = getDataService();
    
    // Check for missing assets and fetch them
    const missingAssets = await dataService.checkMissingAssets(body.assets);
    if (missingAssets.length > 0) {
      console.log(`[API] Fetching ${missingAssets.length} missing assets...`);
      const baseUrl = process.env.VERCEL_URL 
        ? `https://${process.env.VERCEL_URL}` 
        : 'https://fargason-capital-platform-ttgo.vercel.app';
      await dataService.fetchMissingAssets(missingAssets, baseUrl);
    }
    
    // Fetch asset return data
    const fetchStart = Date.now();
    const assetReturns = await dataService.fetchAssetReturns(
      body.assets,
      body.startDate,
      body.endDate
    );
    console.log(`[API] Data fetch: ${Date.now() - fetchStart}ms, rows: ${assetReturns.length}`);
    
    if (assetReturns.length === 0) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'No data found for specified assets and date range' 
        },
        { status: 404, headers: corsHeaders() }
      );
    }
    
    // Build portfolio configuration
    const config: PortfolioConfig = {
      assets: body.assets,
      weights: body.weights,
      startDate: body.startDate,
      endDate: body.endDate,
      rebalanceMonths: body.rebalanceMonths ?? -1
    };
    
    // Calculate portfolio (this is where the magic happens!)
    const calcStart = Date.now();
    const results = calculatePortfolio(
      assetReturns, 
      config,
      body.riskFreeRate // Custom risk-free rate if provided
    );
    console.log(`[API] Calculation: ${Date.now() - calcStart}ms, months: ${results.monthlyReturns.length}`);
    
    // Generate CSV if requested
    let csvFilename = '';
    if (body.generateCSV) {
      try {
        const csvStart = Date.now();
        const csv = generateCSV(results);
        csvFilename = await saveCSVLog(csv);
        console.log(`[API] CSV generation: ${Date.now() - csvStart}ms`);
      } catch (csvError) {
        console.error('CSV generation failed:', csvError);
        csvFilename = 'ERROR: CSV generation failed';
      }
    }
    
    // Build response
    const totalTime = Date.now() - startTime;
    console.log(`[API] Total time: ${totalTime}ms`);
    
    return NextResponse.json({
      success: true,
      portfolio: {
        assets: results.config.assets,
        weights: results.config.weights,
        startDate: results.config.startDate,
        endDate: results.config.endDate,
        rebalanceMonths: results.config.rebalanceMonths
      },
      results: {
        monthlySeries: results.timeSeries,
        ...results.metrics
      },
      logFile: csvFilename || undefined,
      performance: {
        totalTimeMs: totalTime,
        dataPoints: results.monthlyReturns.length
      }
    }, { headers: corsHeaders() });
    
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const totalTime = Date.now() - startTime;
    console.error(`[API ERROR] ${errorMessage} (after ${totalTime}ms)`);
    
    // Add helpful timeout message
    if (totalTime > 9000) {
      return NextResponse.json(
        { 
          success: false, 
          error: `Request timeout after ${totalTime}ms. Try reducing date range or disabling CSV generation.` 
        },
        { status: 500, headers: corsHeaders() }
      );
    }
    
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500, headers: corsHeaders() }
    );
  }
}

