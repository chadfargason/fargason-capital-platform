/**
 * Core Portfolio Calculator - Pure calculation logic
 * 
 * This module contains ONLY the mathematical calculations for portfolio analysis.
 * It has NO dependencies on:
 * - HTTP frameworks (Next.js, Express, etc.)
 * - Databases (Supabase, etc.)
 * - File systems
 * - External APIs
 * 
 * This makes it:
 * - Reusable across different tools (API, CLI, chatbot, web calculator)
 * - Easy to test (just pass data, check output)
 * - Easy to maintain (one place for all calculation logic)
 */

// ============================================================================
// Type Definitions
// ============================================================================

export interface AssetReturn {
  asset: string;
  date: string;
  return: number;
}

export interface PortfolioConfig {
  assets: string[];
  weights: number[];
  startDate: string;
  endDate: string;
  rebalanceMonths?: number; // -1 = never rebalance, >0 = rebalance every N months
}

export interface MonthlyPortfolioReturn {
  date: string;
  portfolioReturn: number;
  cumulativeValue: number;
  assetReturns: Record<string, number>;
  weightsBeforeRebalance: Record<string, number>;
  weightsAfterRebalance: Record<string, number>;
  wasRebalanced: boolean;
}

export interface PortfolioMetrics {
  totalReturn: number;
  totalReturnPercent: number;
  annualizedReturn: number;
  annualizedReturnPercent: number;
  volatility: number;
  volatilityPercent: number;
  sharpeRatio: number;
  maxDrawdown: number;
  maxDrawdownPercent: number;
  sortinoRatio: number;
  calmarRatio: number;
  numMonths: number;
  numYears: number;
  bestMonth: number;
  worstMonth: number;
}

export interface PortfolioResults {
  config: PortfolioConfig;
  monthlyReturns: MonthlyPortfolioReturn[];
  timeSeries: Array<{ date: string; value: number }>;
  metrics: PortfolioMetrics;
}

// ============================================================================
// Validation Functions
// ============================================================================

export function validatePortfolioConfig(config: PortfolioConfig): { valid: boolean; error?: string } {
  if (!config.assets || config.assets.length === 0) {
    return { valid: false, error: 'At least one asset is required' };
  }

  if (!config.weights || config.weights.length === 0) {
    return { valid: false, error: 'Weights array is required' };
  }

  if (config.assets.length !== config.weights.length) {
    return { valid: false, error: 'Assets and weights arrays must have the same length' };
  }

  const weightSum = config.weights.reduce((a, b) => a + b, 0);
  if (Math.abs(weightSum - 1.0) > 0.01) {
    return { valid: false, error: `Weights must sum to 1.0 (currently ${weightSum.toFixed(3)})` };
  }

  const rebalanceMonths = config.rebalanceMonths ?? -1;
  if (rebalanceMonths !== -1 && (rebalanceMonths < 1 || !Number.isInteger(rebalanceMonths))) {
    return { valid: false, error: 'rebalanceMonths must be -1 (never) or a positive integer' };
  }

  return { valid: true };
}

// ============================================================================
// Data Preparation Functions
// ============================================================================

/**
 * Group returns by date for efficient lookup
 * Returns a Map where each date maps to another Map of asset -> return
 */
export function groupReturnsByDate(returns: AssetReturn[]): Map<string, Map<string, number>> {
  const returnsByDate = new Map<string, Map<string, number>>();
  
  for (const row of returns) {
    let dateMap = returnsByDate.get(row.date);
    if (!dateMap) {
      dateMap = new Map();
      returnsByDate.set(row.date, dateMap);
    }
    dateMap.set(row.asset, row.return);
  }
  
  return returnsByDate;
}

/**
 * Filter dates to only include months where ALL assets have data
 */
export function getCompleteDates(
  returnsByDate: Map<string, Map<string, number>>,
  assets: string[]
): string[] {
  const completeDates: string[] = [];
  
  for (const [date, assetReturns] of returnsByDate) {
    const hasAllAssets = assets.every(asset => assetReturns.has(asset));
    if (hasAllAssets) {
      completeDates.push(date);
    }
  }
  
  return completeDates.sort();
}

// ============================================================================
// Core Calculation Functions
// ============================================================================

/**
 * Calculate portfolio returns with optional rebalancing
 * This is the heart of the calculator - pure mathematical logic
 */
export function calculatePortfolioReturns(
  returnsByDate: Map<string, Map<string, number>>,
  config: PortfolioConfig
): MonthlyPortfolioReturn[] {
  const monthlyReturns: MonthlyPortfolioReturn[] = [];
  const rebalanceMonths = config.rebalanceMonths ?? -1;
  
  // Get only dates where all assets have data
  const completeDates = getCompleteDates(returnsByDate, config.assets);
  
  if (completeDates.length === 0) {
    return [];
  }
  
  let cumulativeValue = 1.0;
  const currentWeights = [...config.weights];
  let monthsSinceRebalance = 0;
  
  const assetCount = config.assets.length;
  const newWeights = new Array(assetCount);
  
  for (const date of completeDates) {
    const assetReturns = returnsByDate.get(date)!;
    
    // Calculate weighted portfolio return using current weights
    let monthlyReturn = 0;
    const assetReturnsObj: Record<string, number> = {};
    const weightsBeforeRebalance: Record<string, number> = {};
    
    for (let i = 0; i < assetCount; i++) {
      const asset = config.assets[i];
      const assetReturn = assetReturns.get(asset) || 0;
      
      assetReturnsObj[asset] = assetReturn;
      weightsBeforeRebalance[asset] = currentWeights[i];
      
      // Portfolio return is weighted by current weights
      monthlyReturn += currentWeights[i] * assetReturn;
      
      // Calculate new weight after this month's returns (before rebalancing)
      newWeights[i] = currentWeights[i] * (1 + assetReturn);
    }
    
    // Normalize new weights by portfolio growth
    const portfolioGrowth = 1 + monthlyReturn;
    for (let i = 0; i < assetCount; i++) {
      newWeights[i] = newWeights[i] / portfolioGrowth;
    }
    
    // Update cumulative value
    cumulativeValue *= portfolioGrowth;
    monthsSinceRebalance++;
    
    // Check if we need to rebalance
    const shouldRebalance = rebalanceMonths > 0 && monthsSinceRebalance >= rebalanceMonths;
    const weightsAfterRebalance: Record<string, number> = {};
    
    if (shouldRebalance) {
      // Reset to original weights
      for (let i = 0; i < assetCount; i++) {
        currentWeights[i] = config.weights[i];
        weightsAfterRebalance[config.assets[i]] = config.weights[i];
      }
      monthsSinceRebalance = 0;
    } else {
      // Use the drifted weights
      for (let i = 0; i < assetCount; i++) {
        currentWeights[i] = newWeights[i];
        weightsAfterRebalance[config.assets[i]] = newWeights[i];
      }
    }
    
    monthlyReturns.push({
      date,
      portfolioReturn: monthlyReturn,
      cumulativeValue: parseFloat(cumulativeValue.toFixed(6)),
      assetReturns: assetReturnsObj,
      weightsBeforeRebalance,
      weightsAfterRebalance,
      wasRebalanced: shouldRebalance
    });
  }
  
  return monthlyReturns;
}

/**
 * Calculate portfolio metrics (Sharpe, volatility, drawdown, etc.)
 */
export function calculateMetrics(
  monthlyReturns: MonthlyPortfolioReturn[],
  riskFreeRate: number = 0.02 // Default 2% annual risk-free rate
): PortfolioMetrics {
  if (monthlyReturns.length === 0) {
    throw new Error('Cannot calculate metrics with no return data');
  }
  
  const numMonths = monthlyReturns.length;
  const numYears = numMonths / 12;
  
  // Total and annualized returns
  const finalValue = monthlyReturns[numMonths - 1].cumulativeValue;
  const totalReturn = finalValue - 1;
  const annualizedReturn = numYears > 0 ? Math.pow(finalValue, 1 / numYears) - 1 : 0;
  
  // Volatility
  const returns = monthlyReturns.map(r => r.portfolioReturn);
  const avgReturn = returns.reduce((sum, r) => sum + r, 0) / numMonths;
  const variance = returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / numMonths;
  const monthlyVolatility = Math.sqrt(variance);
  const annualizedVolatility = monthlyVolatility * Math.sqrt(12);
  
  // Sharpe Ratio (with risk-free rate)
  const monthlyRiskFreeRate = Math.pow(1 + riskFreeRate, 1/12) - 1;
  const excessReturns = returns.map(r => r - monthlyRiskFreeRate);
  const avgExcessReturn = excessReturns.reduce((sum, r) => sum + r, 0) / numMonths;
  const annualizedExcessReturn = Math.pow(1 + avgExcessReturn, 12) - 1;
  const sharpeRatio = annualizedVolatility > 0 ? annualizedExcessReturn / annualizedVolatility : 0;
  
  // Sortino Ratio (only penalize downside volatility)
  const downsideReturns = returns.filter(r => r < monthlyRiskFreeRate);
  const downsideVariance = downsideReturns.reduce((sum, r) => sum + Math.pow(r - monthlyRiskFreeRate, 2), 0) / numMonths;
  const downsideVolatility = Math.sqrt(downsideVariance) * Math.sqrt(12);
  const sortinoRatio = downsideVolatility > 0 ? annualizedExcessReturn / downsideVolatility : 0;
  
  // Maximum Drawdown
  let maxValue = 1.0;
  let maxDrawdown = 0;
  
  for (const month of monthlyReturns) {
    maxValue = Math.max(maxValue, month.cumulativeValue);
    const drawdown = (month.cumulativeValue - maxValue) / maxValue;
    maxDrawdown = Math.min(maxDrawdown, drawdown);
  }
  
  // Calmar Ratio (annualized return / max drawdown)
  const calmarRatio = maxDrawdown < 0 ? annualizedReturn / Math.abs(maxDrawdown) : 0;
  
  // Best and worst months
  const bestMonth = Math.max(...returns);
  const worstMonth = Math.min(...returns);
  
  return {
    totalReturn: parseFloat(totalReturn.toFixed(6)),
    totalReturnPercent: parseFloat((totalReturn * 100).toFixed(2)),
    annualizedReturn: parseFloat(annualizedReturn.toFixed(6)),
    annualizedReturnPercent: parseFloat((annualizedReturn * 100).toFixed(2)),
    volatility: parseFloat(annualizedVolatility.toFixed(6)),
    volatilityPercent: parseFloat((annualizedVolatility * 100).toFixed(2)),
    sharpeRatio: parseFloat(sharpeRatio.toFixed(3)),
    maxDrawdown: parseFloat(maxDrawdown.toFixed(6)),
    maxDrawdownPercent: parseFloat((maxDrawdown * 100).toFixed(2)),
    sortinoRatio: parseFloat(sortinoRatio.toFixed(3)),
    calmarRatio: parseFloat(calmarRatio.toFixed(3)),
    numMonths,
    numYears: parseFloat(numYears.toFixed(2)),
    bestMonth: parseFloat(bestMonth.toFixed(6)),
    worstMonth: parseFloat(worstMonth.toFixed(6))
  };
}

/**
 * Main entry point - calculates complete portfolio results
 * This is what other tools should call
 */
export function calculatePortfolio(
  returns: AssetReturn[],
  config: PortfolioConfig,
  riskFreeRate?: number
): PortfolioResults {
  // Validate configuration
  const validation = validatePortfolioConfig(config);
  if (!validation.valid) {
    throw new Error(validation.error);
  }
  
  // Group data by date
  const returnsByDate = groupReturnsByDate(returns);
  
  // Calculate monthly returns
  const monthlyReturns = calculatePortfolioReturns(returnsByDate, config);
  
  if (monthlyReturns.length === 0) {
    throw new Error('No overlapping data found for all assets in date range');
  }
  
  // Build time series
  const timeSeries = monthlyReturns.map(r => ({
    date: r.date,
    value: r.cumulativeValue
  }));
  
  // Calculate metrics
  const metrics = calculateMetrics(monthlyReturns, riskFreeRate);
  
  return {
    config,
    monthlyReturns,
    timeSeries,
    metrics
  };
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Generate CSV from portfolio results
 */
export function generateCSV(results: PortfolioResults): string {
  const { config, monthlyReturns } = results;
  
  // Header row
  const headers = [
    'Date',
    ...config.assets,
    'Portfolio_Return',
    ...config.assets.map(a => `${a}_Weight_Before`),
    ...config.assets.map(a => `${a}_Weight_After`),
    'Rebalanced'
  ];
  
  const rows: string[] = new Array(monthlyReturns.length + 1);
  rows[0] = headers.join(',');
  
  // Data rows
  for (let i = 0; i < monthlyReturns.length; i++) {
    const entry = monthlyReturns[i];
    const rowData: string[] = [entry.date];
    
    // Asset returns
    for (const asset of config.assets) {
      rowData.push(entry.assetReturns[asset]?.toFixed(6) || '0');
    }
    
    // Portfolio return
    rowData.push(entry.portfolioReturn.toFixed(6));
    
    // Weights before rebalance
    for (const asset of config.assets) {
      rowData.push(entry.weightsBeforeRebalance[asset]?.toFixed(6) || '0');
    }
    
    // Weights after rebalance
    for (const asset of config.assets) {
      rowData.push(entry.weightsAfterRebalance[asset]?.toFixed(6) || '0');
    }
    
    // Rebalanced flag
    rowData.push(entry.wasRebalanced ? 'YES' : 'NO');
    
    rows[i + 1] = rowData.join(',');
  }
  
  return rows.join('\n');
}
