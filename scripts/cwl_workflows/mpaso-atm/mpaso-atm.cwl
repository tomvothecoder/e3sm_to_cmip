#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: Workflow

requirements:
  - class: ScatterFeatureRequirement
  - class: SubworkflowFeatureRequirement
  - class: InlineJavascriptRequirement

inputs:

  frequency: int
  start_year: int
  end_year: int
  timeout: int

  atm_data_path: string
  std_var_list: string[]

  mpas_data_path: string
  mpas_var_list: string[]

  num_workers: int
  casename: string

  hrz_atm_map_path: string
  mpas_map_path: string 
  mpas_restart_path: string
  mpas_region_path: string
  mpas_namelist_path: string

  tables_path: string
  metadata_path: string
  

outputs:
  cmorized:
    type: 
      Directory[]
    outputSource: 
      step_run_mpaso/cmorized

steps:

  step_segments:
    run: 
      generate_segments.cwl
    in:
      start: start_year
      end: end_year
      frequency: frequency
    out:
      - segments_start
      - segments_end

  step_discover_atm_files:
    run: 
      discover_atm_files.cwl
    scatter:
      - start
      - end
    scatterMethod:
      dotproduct
    in:
      input: atm_data_path
      start: step_segments/segments_start
      end: step_segments/segments_end
    out:
      - atm_files
  
  step_hrz_remap:
    run: 
      hrzremap_stdin.cwl
    scatter:
      - input_files
      - start_year
      - end_year
    scatterMethod:
      dotproduct
    in:
      year_per_file: frequency
      casename: casename
      start_year: step_segments/segments_start
      end_year: step_segments/segments_end
      map_path: hrz_atm_map_path
      input_files: step_discover_atm_files/atm_files
    out:
      - time_series_files
  
  step_run_mpaso:
    run:
      mpaso.cwl
    in:
      frequency: frequency
      start_year: start_year
      end_year: end_year
      data_path: mpas_data_path
      map_path: mpas_map_path
      namelist_path: mpas_namelist_path
      restart_path: mpas_restart_path
      psl_files: step_hrz_remap/time_series_files
      region_path: mpas_region_path
      tables_path: tables_path
      metadata_path: metadata_path
      cmor_var_list: mpas_var_list
      num_workers: num_workers
      timeout: timeout
    out:
      - cmorized