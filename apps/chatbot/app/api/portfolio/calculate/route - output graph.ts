import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';
import { writeFile } from 'fs/promises';
import { join } from 'path';

interface CalculateRequest {
  assets: string[];
  weights: number[];
  startDate: string;
  endDate: string;
  rebalanceMonths?: number; // NEW: Optional rebalancing parameter
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
  currentWeights: { [key: string]: number }; // NEW: Track current weights
}

// CORS headers helper
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Generate CSV from monthly data
function generateCSV(monthlyData: MonthlyLogEntry[], assets: string[]): string {
  // Header row - now includes current weights
  const headers = ['Date', ...assets, 'Portfolio_Return', ...assets.map(a => `${a}_Weight`)];
  let csv = headers.join(',') + '\n';
  
  // Data rows
  monthlyData.forEach(entry => {
    const row = [
      entry.date,
      ...assets.map(asset => entry.assetReturns[asset]?.toFixed(6) || '0'),
      entry.portfolioReturn.toFixed(6),
      ...assets.map(asset => entry.currentWeights[asset]?.toFixed(6) || '0')
    ];
    csv += row.join(',') + '\n';
  });
  
  return csv;
}

// Save CSV to file
async function saveCSVLog(csv: string): Promise<string> {
  try {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `Returns_Log_${timestamp}.csv`;
    
    // Use /tmp directory (works on both local and Vercel)
    const filepath = join('/tmp', filename);
    // const filepath = join('C:\\logs', filename) could be needed
    
    await writeFile(filepath, csv, 'utf-8');
    console.log(`✓ CSV log saved to: ${filepath}`);
    
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

    // NEW: Get rebalancing parameter (default to -1 = never rebalance)
    const rebalanceMonths = body.rebalanceMonths ?? -1;
    
    if (rebalanceMonths !== -1 && (rebalanceMonths < 1 || !Number.isInteger(rebalanceMonths))) {
      return NextResponse.json(
        { success: false, error: 'rebalanceMonths must be -1 (never) or a positive integer' },
        { status: 400, headers: corsHeaders() }
      );
    }

    // Fetch data from Supabase
    const { data, error } = await supabase
      .from('asset_returns')
      .select('asset_ticker, return_date, monthly_return')
      .in('asset_ticker', body.assets)
      .gte('return_date', body.startDate)
      .lte('return_date', body.endDate)
      .order('return_date');

    if (error) throw error;

    if (!data || data.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No data found for specified assets and date range' },
        { status: 404, headers: corsHeaders() }
      );
    }

    // Group returns by date
    const returnsByDate = new Map<string, Map<string, number>>();
    
    (data as AssetReturnData[]).forEach((row) => {
      if (!returnsByDate.has(row.return_date)) {
        returnsByDate.set(row.return_date, new Map());
      }
      const dateMap = returnsByDate.get(row.return_date);
      if (dateMap) {
        dateMap.set(row.asset_ticker, parseFloat(row.monthly_return));
      }
    });

    // NEW: Calculate portfolio returns with rebalancing logic
    const monthlyReturns: { date: string; return: number }[] = [];
    const monthlySeries: { date: string; value: number }[] = [];
    const monthlyLogData: MonthlyLogEntry[] = [];
    let cumulativeReturn = 1.0;
    monthlySeries.push({ date: body.startDate.slice(0, 7), value: 1.000000 });
    
    // Track current weights (start with initial weights)
    const currentWeights = [...body.weights];
    
    // Track months since last rebalance
    let monthsSinceRebalance = 0;

    for (const [date, assetReturns] of returnsByDate) {
      const hasAllAssets = body.assets.every(asset => assetReturns.has(asset));
      
      if (!hasAllAssets) {
        continue;
      }

      // Calculate weighted portfolio return for this month using CURRENT weights
      let monthlyReturn = 0;
      const assetReturnsObj: { [key: string]: number } = {};
      const newWeights: number[] = new Array(body.assets.length);
      
      for (let i = 0; i < body.assets.length; i++) {
        const assetReturn = assetReturns.get(body.assets[i]) || 0;
        assetReturnsObj[body.assets[i]] = assetReturn;
        
        // Portfolio return is weighted by current weights
        monthlyReturn += currentWeights[i] * assetReturn;
        
        // Calculate new weight after this month's returns (before rebalancing)
        // New weight = old weight * (1 + asset return) / (1 + portfolio return)
        newWeights[i] = currentWeights[i] * (1 + assetReturn);
      }
      
      // Normalize new weights by the portfolio return
      const portfolioGrowth = 1 + monthlyReturn;
      for (let i = 0; i < newWeights.length; i++) {
        newWeights[i] = newWeights[i] / portfolioGrowth;
      }
      
      // Update cumulative return
      cumulativeReturn *= portfolioGrowth;

      // NEW: append the cumulative value for this month
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
        for (let i = 0; i < body.assets.length; i++) {
          currentWeights[i] = body.weights[i];
        }
        monthsSinceRebalance = 0;
      } else {
        // Use the drifted weights
        for (let i = 0; i < newWeights.length; i++) {
          currentWeights[i] = newWeights[i];
        }
      }
      
      // Store for main calculation
      monthlyReturns.push({
        date: date,
        return: monthlyReturn
      });

      // Store for CSV log (record weights BEFORE next month's rebalancing)
      const currentWeightsObj: { [key: string]: number } = {};
      for (let i = 0; i < body.assets.length; i++) {
        currentWeightsObj[body.assets[i]] = newWeights[i]; // Log the drifted weights
      }
      
      monthlyLogData.push({
        date: date,
        assetReturns: assetReturnsObj,
        portfolioReturn: monthlyReturn,
        currentWeights: currentWeightsObj
      });
    }

    if (monthlyReturns.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No overlapping data found for all assets in date range' },
        { status: 404, headers: corsHeaders() }
      );
    }

    // Generate and save CSV log
    let csvFilename = '';
    try {
      const csv = generateCSV(monthlyLogData, body.assets);
      csvFilename = await saveCSVLog(csv);
    } catch (csvError) {
      console.error('CSV logging failed:', csvError);
      // Continue with calculation even if CSV fails
    }

    // Calculate statistics
    const totalReturn = cumulativeReturn - 1;
    const numMonths = monthlyReturns.length;
    const numYears = numMonths / 12;
    const annualizedReturn = numYears > 0 ? Math.pow(cumulativeReturn, 1 / numYears) - 1 : 0;

    const avgReturn = monthlyReturns.reduce((sum, r) => sum + r.return, 0) / numMonths;
    const variance = monthlyReturns.reduce((sum, r) => sum + Math.pow(r.return - avgReturn, 2), 0) / numMonths;
    const monthlyVolatility = Math.sqrt(variance);
    const annualizedVolatility = monthlyVolatility * Math.sqrt(12);

    return NextResponse.json({
      success: true,
      portfolio: {
        assets: body.assets,
        weights: body.weights,
        startDate: body.startDate,
        endDate: body.endDate,
        rebalanceMonths: rebalanceMonths // NEW: Include in response
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
      logFile: csvFilename // Include filename in response
    }, { headers: corsHeaders() });

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Calculate endpoint error:', errorMessage);
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500, headers: corsHeaders() }
    );
  }
}

// TODO: Add `monthlySeries` to your results object using `toMonthlySeries` based on your monthly returns/values array.
