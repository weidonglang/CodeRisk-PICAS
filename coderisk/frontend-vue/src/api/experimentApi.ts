import { getApi, type ApiResponse } from './http'

export interface ExperimentMetricRow {
  method: string
  sampleCount: number
  precision: number
  recall: number
  f1: number
  accuracy: number
  falsePositiveRate: number
  falseNegativeRate: number
  naturalSimilarityFpr?: number
}

export interface ExperimentSummary {
  run: {
    runId: string
    formulaVersion: string
    algorithmVersion: string
    datasetVersion: string
    randomSeed: number
    gitCommit: string
    caseCount: number
    validationCaseCount: number
    testCaseCount: number
    validationProblemCount: number
    testProblemCount: number
    calibrationPolicy: string
  }
  validationCalibration: {
    selectedFixedThreshold: number
    productionDynamicFormulaChanged: boolean
  }
  E1_fixedVsDynamic: ExperimentMetricRow[]
  E2_rawVsCanonical: {
    caseCount: number
    meanRawTokenSimilarity: number
    meanCanonicalTokenSimilarity: number
    meanCanonicalGain: number
  }
  E3_fusion: ExperimentMetricRow[]
  E4_ablation: ExperimentMetricRow[]
  E5_failureAnalysis: {
    failureCount: number
    borderlineCount: number
    parserFallbackCount: number
  }
}

export interface LatestExperiment {
  runId: string
  summary: ExperimentSummary
  reportFile: string
}

export async function getLatestExperiment(): Promise<ApiResponse<LatestExperiment>> {
  return getApi<LatestExperiment>('/experiments/latest')
}
