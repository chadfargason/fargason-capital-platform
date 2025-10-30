/**
 * Portfolio Data Service
 * 
 * This module handles ALL data fetching and storage operations.
 * It abstracts away the database (Supabase) from the calculation logic.
 * 
 * Benefits:
 * - Easy to swap databases (could use PostgreSQL, MySQL, etc.)
 * - Easy to add caching layer
 * - Separates I/O from business logic
 * - Makes testing easier (can mock data service)
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js';
import type { AssetReturn } from './portfolioCalculator';

// ============================================================================
// Type Definitions
// ============================================================================

interface SupabaseAssetReturn {
  asset_ticker: string;
  return_date: string;
  monthly_return: string;
}

export interface DataServiceConfig {
  supabaseUrl: string;
  supabaseKey: string;
}

// ============================================================================
// Portfolio Data Service Class
// ============================================================================

export class PortfolioDataService {
  private supabase: SupabaseClient;
  
  constructor(config: DataServiceConfig) {
    this.supabase = createClient(config.supabaseUrl, config.supabaseKey);
  }
  
  /**
   * Fetch asset returns from database
   */
  async fetchAssetReturns(
    assets: string[],
    startDate: string,
    endDate: string
  ): Promise<AssetReturn[]> {
    const { data, error } = await this.supabase
      .from('asset_returns')
      .select('asset_ticker, return_date, monthly_return')
      .in('asset_ticker', assets)
      .gte('return_date', startDate)
      .lte('return_date', endDate)
      .order('return_date');
    
    if (error) {
      throw new Error(`Database error: ${error.message}`);
    }
    
    if (!data || data.length === 0) {
      return [];
    }
    
    // Convert from database format to calculator format
    return (data as SupabaseAssetReturn[]).map(row => ({
      asset: row.asset_ticker,
      date: row.return_date,
      return: parseFloat(row.monthly_return)
    }));
  }
  
  /**
   * Check which assets are missing from the database
   */
  async checkMissingAssets(assets: string[]): Promise<string[]> {
    try {
      const { data, error } = await this.supabase
        .from('asset_returns')
        .select('asset_ticker')
        .in('asset_ticker', assets);
      
      if (error) {
        console.error('Error checking missing assets:', error);
        return assets; // If we can't check, assume all are missing
      }
      
      const existingAssets = new Set(
        data?.map((row: { asset_ticker: string }) => row.asset_ticker) || []
      );
      
      return assets.filter(asset => !existingAssets.has(asset));
    } catch (error) {
      console.error('Error in checkMissingAssets:', error);
      return assets;
    }
  }
  
  /**
   * Fetch missing assets using the add-asset API endpoint
   */
  async fetchMissingAssets(
    missingAssets: string[],
    baseUrl: string
  ): Promise<{ success: number; failed: number }> {
    if (missingAssets.length === 0) {
      return { success: 0, failed: 0 };
    }
    
    console.log(`[Data Service] Fetching ${missingAssets.length} missing assets: ${missingAssets.join(', ')}`);
    
    let successCount = 0;
    let failedCount = 0;
    
    for (const ticker of missingAssets) {
      try {
        console.log(`[Data Service] Processing ${ticker} (${successCount + failedCount + 1}/${missingAssets.length})`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 45000);
        
        const response = await fetch(`${baseUrl}/api/portfolio/add-asset`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticker }),
          signal: controller.signal,
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          const result = await response.json();
          if (result.success) {
            successCount++;
            console.log(`[Data Service] ✓ ${ticker}: ${result.message}`);
          } else {
            failedCount++;
            console.log(`[Data Service] ✗ ${ticker}: ${result.message}`);
          }
        } else {
          failedCount++;
          const errorText = await response.text();
          console.log(`[Data Service] ✗ ${ticker}: HTTP ${response.status} - ${errorText}`);
        }
        
        // Rate limiting: wait between requests
        if (successCount + failedCount < missingAssets.length) {
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      } catch (error) {
        failedCount++;
        console.log(`[Data Service] ✗ ${ticker}: ${error}`);
      }
    }
    
    console.log(`[Data Service] Complete: ${successCount} success, ${failedCount} failed`);
    return { success: successCount, failed: failedCount };
  }
  
  /**
   * Get available assets from the database
   */
  async getAvailableAssets(): Promise<string[]> {
    const { data, error } = await this.supabase
      .from('asset_returns')
      .select('asset_ticker')
      .limit(1000);
    
    if (error) {
      throw new Error(`Database error: ${error.message}`);
    }
    
    const uniqueAssets = new Set(
      data?.map((row: { asset_ticker: string }) => row.asset_ticker) || []
    );
    
    return Array.from(uniqueAssets).sort();
  }
  
  /**
   * Get date range for a specific asset
   */
  async getAssetDateRange(asset: string): Promise<{ startDate: string; endDate: string } | null> {
    const { data, error } = await this.supabase
      .from('asset_returns')
      .select('return_date')
      .eq('asset_ticker', asset)
      .order('return_date', { ascending: true });
    
    if (error || !data || data.length === 0) {
      return null;
    }
    
    return {
      startDate: data[0].return_date,
      endDate: data[data.length - 1].return_date
    };
  }
}

// ============================================================================
// Singleton Factory (for convenience)
// ============================================================================

let dataServiceInstance: PortfolioDataService | null = null;

export function getDataService(): PortfolioDataService {
  if (!dataServiceInstance) {
    if (!process.env.SUPABASE_URL || !process.env.SUPABASE_KEY) {
      throw new Error('Missing environment variables: SUPABASE_URL or SUPABASE_KEY');
    }
    
    dataServiceInstance = new PortfolioDataService({
      supabaseUrl: process.env.SUPABASE_URL,
      supabaseKey: process.env.SUPABASE_KEY
    });
  }
  
  return dataServiceInstance;
}

/**
 * Create a new data service instance (useful for testing or multiple configs)
 */
export function createDataService(config: DataServiceConfig): PortfolioDataService {
  return new PortfolioDataService(config);
}
