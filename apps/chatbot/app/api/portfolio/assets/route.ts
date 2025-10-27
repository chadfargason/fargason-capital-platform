import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';

// CORS headers helper
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Handle OPTIONS request (preflight)
export async function OPTIONS() {
  return NextResponse.json({}, { headers: corsHeaders() });
}

interface AssetReturn {
  asset_ticker: string;
  return_date: string;
}

interface AssetSummary {
  ticker: string;
  startDate: string;
  endDate: string;
  months: number;
}

export async function GET() {
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

    // Create Supabase client (do this inside the function, not at module level)
    const supabase = createClient(
      process.env.SUPABASE_URL,
      process.env.SUPABASE_KEY
    );

    // Fetch all data using pagination
    let allData: AssetReturn[] = [];
    let page = 0;
    const pageSize = 1000;
    let hasMore = true;

    while (hasMore) {
      const from = page * pageSize;
      const to = from + pageSize - 1;

      const { data, error } = await supabase
        .from('asset_returns')
        .select('asset_ticker, return_date')
        .order('asset_ticker')
        .order('return_date')
        .range(from, to);

      if (error) throw error;

      if (data && data.length > 0) {
        allData = allData.concat(data as AssetReturn[]);
        page++;
        
        if (data.length < pageSize) {
          hasMore = false;
        }
      } else {
        hasMore = false;
      }
    }

    // Group by asset ticker
    const assetMap = new Map<string, AssetSummary>();
    
    allData.forEach((row) => {
      if (!assetMap.has(row.asset_ticker)) {
        assetMap.set(row.asset_ticker, {
          ticker: row.asset_ticker,
          startDate: row.return_date,
          endDate: row.return_date,
          months: 0
        });
      }
      const asset = assetMap.get(row.asset_ticker);
      if (asset) {
        asset.endDate = row.return_date;
        asset.months++;
      }
    });

    const assets = Array.from(assetMap.values());

    return NextResponse.json({
      success: true,
      count: assets.length,
      assets: assets
    }, { headers: corsHeaders() });

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Assets endpoint error:', errorMessage);
    return NextResponse.json(
      { success: false, error: errorMessage },
      { status: 500, headers: corsHeaders() }
    );
  }
}