import { createClient } from '@supabase/supabase-js';
import { NextResponse } from 'next/server';
import { spawn } from 'child_process';
import { join } from 'path';

// Add asset API endpoint - triggers automatic asset fetching
// This endpoint allows the portfolio calculator to automatically fetch missing assets
// Version: Latest with TypeScript warnings fixed

interface AddAssetRequest {
  ticker: string;
}

interface AssetResponse {
  success: boolean;
  message: string;
  action: 'exists' | 'added' | 'fetch_failed' | 'upload_failed' | 'error';
  data_points?: number;
  date_range?: {
    start: string;
    end: string;
  };
}

// CORS headers helper
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

// Check if asset exists in database
async function checkAssetExists(ticker: string): Promise<boolean> {
  const supabase = createClient(
    process.env.SUPABASE_URL!,
    process.env.SUPABASE_KEY!
  );

  try {
    const { data, error } = await supabase
      .from('asset_returns')
      .select('asset_ticker')
      .eq('asset_ticker', ticker)
      .limit(1);

    if (error) {
      console.error('Error checking asset existence:', error);
      return false;
    }

    return data && data.length > 0;
  } catch (error) {
    console.error('Error checking asset existence:', error);
    return false;
  }
}

// Add new asset using Python script
async function addNewAsset(ticker: string): Promise<AssetResponse> {
  return new Promise((resolve) => {
    const pythonScript = join(process.cwd(), 'services', 'data-pipeline', 'add_new_asset.py');
    
    const python = spawn('python', [pythonScript, ticker]);
    
    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          const result = JSON.parse(output);
          resolve(result);
        } catch {
          resolve({
            success: false,
            message: `Failed to parse Python output: ${output}`,
            action: 'error'
          });
        }
      } else {
        resolve({
          success: false,
          message: `Python script failed: ${error}`,
          action: 'error'
        });
      }
    });
  });
}

export async function OPTIONS() {
  return new Response(null, {
    status: 200,
    headers: corsHeaders()
  });
}

export async function POST(request: Request) {
  const startTime = Date.now();
  
  try {
    const body: AddAssetRequest = await request.json();
    const { ticker } = body;

    if (!ticker) {
      return NextResponse.json(
        { 
          success: false, 
          error: 'Ticker is required' 
        },
        { status: 400, headers: corsHeaders() }
      );
    }

    const upperTicker = ticker.toUpperCase();
    console.log(`[Add Asset] Processing request for: ${upperTicker}`);

    // Check if asset already exists
    const exists = await checkAssetExists(upperTicker);
    
    if (exists) {
      return NextResponse.json({
        success: true,
        message: `${upperTicker} already exists in database`,
        action: 'exists',
        processing_time_ms: Date.now() - startTime
      }, { headers: corsHeaders() });
    }

    // Add new asset
    const result = await addNewAsset(upperTicker);
    
    return NextResponse.json({
      ...result,
      processing_time_ms: Date.now() - startTime
    }, { headers: corsHeaders() });

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error(`[Add Asset ERROR] ${errorMessage}`);
    
    return NextResponse.json(
      { 
        success: false, 
        error: errorMessage,
        processing_time_ms: Date.now() - startTime
      },
      { status: 500, headers: corsHeaders() }
    );
  }
}
