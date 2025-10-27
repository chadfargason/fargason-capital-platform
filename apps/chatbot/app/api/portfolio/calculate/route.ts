import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';
import { writeFile } from 'fs/promises';
import { join } from 'path';

interface CalculateRequest {
  assets: string[];
  weights: number[];
  startDate: string;
  endDate: string;
  rebalanceMonths?: number;
  generateCSV?: boolean; // NEW: Make CSV generation optional
}

interface AssetReturnData {
  asset_ticker: string;
  return_date: string;
  monthly_return: string;
}

interface MonthlyLogEntry {
  date: string;
  assetReturns: { [key: string]: number };
  portfolioReturn: number;
  currentWeights: { [key: string]: number };
}

// CORS headers helper
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// OPTIMIZED: Generate CSV from monthly data using array.join()
function generateCSV(monthlyData: MonthlyLogEntry[], assets: string[]): string {
  // Header row
  const headers = ['Date', ...assets, 'Portfolio_Return', ...assets.map(a => `${a}_Weight`)];
  
  // Pre-allocate array with known size (header + data rows)
  const rows: string[] = new Array(monthlyData.length + 1);
  rows[0] = headers.join(',');
  
  // Data rows - build each row as array then join
  for (let i = 0; i < monthlyData.length; i++) {
    const entry = monthlyData[i];
    const rowData: string[] = [entry.date];
    
    // Asset returns
    for (const asset of assets) {
      rowData.push(entry.assetReturns[asset]?.toFixed(6) || '0');
    }
    
    // Portfolio return
    rowData.push(entry.portfolioReturn.toFixed(6));
    
    // Current weights
    for (const asset of assets) {
      rowData.push(entry.currentWeights[asset]?.toFixed(6) || '0');
    }
    
    rows[i + 1] = rowData.join(',');
  }
  
  // Single join operation at the end (MUCH faster than string concatenation)
  return rows.join('\n');
}

// Save CSV to file
async function saveCSVLog(csv: string): Promise<string> {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `Returns_Log_${timestamp}.csv`;
    
    // Use /tmp directory (works on both local and Vercel)
    const filepath = join('/tmp', filename);
    
    await writeFile(filepath, csv, 'utf-8');
    console.log(`✓ CSV log saved to: ${filepath} (${(csv.length / 1024).toFixed(1)} KB)`);
    
    return filename;
  } catch (error) {
    console.error('Error saving CSV log:', error);
    throw error;
  }
}

// Handle OPTIONS request (preflight)
export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders() });
}

export async function POST(request: Request) {
  const startTime = Date.now();
  
  try {
    // Check for required environment variables
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
      console.error('Missing environment variables: SUPABASE_URL or SUPABASE_KEY');
      return NextResponse.json(
        { 
          success: false, 
          error: 'Server configuration error: Missing database credentials' 
        },
        { status: 500, headers: corsHeaders() }
      );
    }

    // Create Supabase client
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_KEY
    );

    const body: CalculateRequest = await request.json();
    
    // Validate inputs
    if (!body.assets || !body.weights || !body.startDate || !body.endDate) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: assets, weights, startDate, endDate' },
        { status: 400, headers: corsHeaders() }
      );
    }

    if (body.assets.length !== body.weights.length) {
      return NextResponse.json(
        { success: false, error: 'Assets and weights arrays must have the same length' },
        { status: 400, headers: corsHeaders() }
      );
    }

    const weightSum = body.weights.reduce((a, b) => a + b, 0);
    if (Math.abs(weightSum - 1.0) > 0.01) {
      return NextResponse.json(
        { success: false, error: `Weights must sum to 1.0 (currently ${weightSum.toFixed(3)})` },
        { status: 400, headers: corsHeaders() }
      );
    }

    // Get rebalancing parameter (default to -1 = never rebalance)
    const rebalanceMonths = body.rebalanceMonths ?? -1;
    
    if (rebalanceMonths !== -1 && (rebalanceMonths < 1 || !Number.isInteger(rebalanceMonths))) {
      return NextResponse.json(
        { success: false, error: 'rebalanceMonths must be -1 (never) or a positive integer' },
        { status: 400, headers: corsHeaders() }
      );
    }

    // OPTIMIZED: Check if CSV generation is requested (default: false for better performance)
    const shouldGenerateCSV = body.generateCSV ?? false;

    console.log(`[Portfolio Calc] Assets: ${body.assets.length}, Date range: ${body.startDate} to ${body.endDate}, CSV: ${shouldGenerateCSV}`);

    // Fetch data from Supabase
    const fetchStart = Date.now();
    const { data, error } = await supabase
      .from('asset_returns')
      .select('asset_ticker, return_date, monthly_return')
      .in('asset_ticker', body.assets)
      .gte('return_date', body.startDate)
      .lte('return_date', body.endDate)
      .order('return_date');

    console.log(`[Portfolio Calc] Supabase fetch: ${Date.now() - fetchStart}ms, rows: ${data?.length || 0}`);

    if (error) throw error;

    if (!data || data.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No data found for specified assets and date range' },
        { status: 404, headers: corsHeaders() }
      );
    }

    // OPTIMIZED: Group returns by date using Map for O(1) lookups
    const calcStart = Date.now();
    const returnsByDate = new Map<string, Map<string, number>>();
    
    (data as AssetReturnData[]).forEach((row) => {
      let dateMap = returnsByDate.get(row.return_date);
      if (!dateMap) {
        dateMap = new Map();
        returnsByDate.set(row.return_date, dateMap);
      }
      dateMap.set(row.asset_ticker, parseFloat(row.monthly_return));
    });

    // Calculate portfolio returns with rebalancing logic
    const monthlyReturns: { date: string; return: number }[] = [];
    const monthlySeries: { date: string; value: number }[] = [];
    
    // OPTIMIZED: Only create monthlyLogData if CSV is requested
    const monthlyLogData: MonthlyLogEntry[] = shouldGenerateCSV ? [] : [];
    
    let cumulativeReturn = 1.0;
    monthlySeries.push({ date: body.startDate.slice(0, 7), value: 1.000000 });
    
    // Track current weights (start with initial weights)
    const currentWeights = [...body.weights];
    
    // Track months since last rebalance
    let monthsSinceRebalance = 0;

    // OPTIMIZED: Pre-allocate arrays for better performance
    const assetCount = body.assets.length;
    const newWeights = new Array(assetCount);

    for (const [date, assetReturns] of returnsByDate) {
      const hasAllAssets = body.assets.every(asset => assetReturns.has(asset));
      
      if (!hasAllAssets) {
        continue;
      }

      // Calculate weighted portfolio return for this month using CURRENT weights
      let monthlyReturn = 0;
      let assetReturnsObj: { [key: string]: number } | undefined;
      
      // Only create object if we need CSV
      if (shouldGenerateCSV) {
        assetReturnsObj = {};
      }
      
      for (let i = 0; i < assetCount; i++) {
        const assetReturn = assetReturns.get(body.assets[i]) || 0;
        
        // Only build object if we need CSV
        if (assetReturnsObj) {
          assetReturnsObj[body.assets[i]] = assetReturn;
        }
        
        // Portfolio return is weighted by current weights
        monthlyReturn += currentWeights[i] * assetReturn;
        
        // Calculate new weight after this month's returns (before rebalancing)
        newWeights[i] = currentWeights[i] * (1 + assetReturn);
      }
      
      // Normalize new weights by the portfolio return
      const portfolioGrowth = 1 + monthlyReturn;
      for (let i = 0; i < assetCount; i++) {
        newWeights[i] = newWeights[i] / portfolioGrowth;
      }
      
      // Update cumulative return
      cumulativeReturn *= portfolioGrowth;

      // Append the cumulative value for this month
      monthlySeries.push({
        date,
        value: parseFloat(cumulativeReturn.toFixed(6))
      });
      
      // Increment months counter
      monthsSinceRebalance++;
      
      // Check if we need to rebalance
      const shouldRebalance = rebalanceMonths > 0 && monthsSinceRebalance >= rebalanceMonths;
      
      if (shouldRebalance) {
        // Reset to original weights
        for (let i = 0; i < assetCount; i++) {
          currentWeights[i] = body.weights[i];
        }
        monthsSinceRebalance = 0;
      } else {
        // Use the drifted weights
        for (let i = 0; i < assetCount; i++) {
          currentWeights[i] = newWeights[i];
        }
      }
      
      // Store for main calculation
      monthlyReturns.push({
        date: date,
        return: monthlyReturn
      });

      // OPTIMIZED: Only store CSV data if needed
      if (shouldGenerateCSV) {
        const currentWeightsObj: { [key: string]: number } = {};
        for (let i = 0; i < assetCount; i++) {
          currentWeightsObj[body.assets[i]] = newWeights[i];
        }
        
        monthlyLogData.push({
          date: date,
          assetReturns: assetReturnsObj!, // Non-null assertion: guaranteed to be defined inside this block
          portfolioReturn: monthlyReturn,
          currentWeights: currentWeightsObj
        });
      }
    }

    console.log(`[Portfolio Calc] Calculation: ${Date.now() - calcStart}ms, months processed: ${monthlyReturns.length}`);

    if (monthlyReturns.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No overlapping data found for all assets in date range' },
        { status: 404, headers: corsHeaders() }
      );
    }

    // OPTIMIZED: Only generate and save CSV if requested
    let csvFilename = '';
    if (shouldGenerateCSV) {
      try {
        const csvStart = Date.now();
        const csv = generateCSV(monthlyLogData, body.assets);
        csvFilename = await saveCSVLog(csv);
        console.log(`[Portfolio Calc] CSV generation: ${Date.now() - csvStart}ms`);
      } catch (csvError) {
        console.error('CSV logging failed:', csvError);
        // Continue with calculation even if CSV fails
        csvFilename = 'ERROR: CSV generation failed';
      }
    }

    // Calculate statistics
    const statsStart = Date.now();
    const totalReturn = cumulativeReturn - 1;
    const numMonths = monthlyReturns.length;
    const numYears = numMonths / 12;
    const annualizedReturn = numYears > 0 ? Math.pow(cumulativeReturn, 1 / numYears) - 1 : 0;

    const avgReturn = monthlyReturns.reduce((sum, r) => sum + r.return, 0) / numMonths;
    const variance = monthlyReturns.reduce((sum, r) => sum + Math.pow(r.return - avgReturn, 2), 0) / numMonths;
    const monthlyVolatility = Math.sqrt(variance);
    const annualizedVolatility = monthlyVolatility * Math.sqrt(12);

    console.log(`[Portfolio Calc] Statistics: ${Date.now() - statsStart}ms`);
    console.log(`[Portfolio Calc] Total time: ${Date.now() - startTime}ms`);

    return NextResponse.json({
      success: true,
      portfolio: {
        assets: body.assets,
        weights: body.weights,
        startDate: body.startDate,
        endDate: body.endDate,
        rebalanceMonths: rebalanceMonths
      },
      results: {
        monthlySeries: monthlySeries,
        totalReturn: parseFloat(totalReturn.toFixed(6)),
        totalReturnPercent: parseFloat((totalReturn * 100).toFixed(2)),
        annualizedReturn: parseFloat(annualizedReturn.toFixed(6)),
        annualizedReturnPercent: parseFloat((annualizedReturn * 100).toFixed(2)),
        volatility: parseFloat(annualizedVolatility.toFixed(6)),
        volatilityPercent: parseFloat((annualizedVolatility * 100).toFixed(2)),
        numMonths: numMonths,
        numYears: parseFloat(numYears.toFixed(2)),
        sharpeRatio: annualizedVolatility > 0 ? parseFloat((annualizedReturn / annualizedVolatility).toFixed(2)) : 0
      },
      logFile: csvFilename || undefined, // Only include if CSV was generated
      performance: {
        totalTimeMs: Date.now() - startTime,
        dataPoints: monthlyReturns.length
      }
    }, { headers: corsHeaders() });

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    const totalTime = Date.now() - startTime;
    console.error(`[Portfolio Calc ERROR] ${errorMessage} (after ${totalTime}ms)`);
    
    // Add helpful timeout message
    if (totalTime > 9000) {
      return NextResponse.json(
        { 
          success: false, 
          error: `Request timeout after ${totalTime}ms. Try: (1) reducing date range, (2) disabling CSV generation, or (3) upgrading Vercel plan for longer timeouts.` 
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
