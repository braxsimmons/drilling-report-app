-- ============================================================
-- DAILY DRILLING REPORT — COMPLETE SCHEMA
-- Postgres / Supabase
-- ============================================================

-- ---------- Optional: namespace ----------
-- create schema if not exists public;

-- ============================================================
-- CORE TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_core (
  id                  bigserial PRIMARY KEY,
  report_number       text NOT NULL,
  date                date NOT NULL,
  oil_company         text,
  contractor          text,
  well_name           text NOT NULL,
  location            text,
  county_state        text,
  permit_number       text,
  api_number          text,
  rig_contractor_no   text,
  depth_0000_ft       numeric,
  depth_2400_ft       numeric,
  footage_today_ft    numeric,
  rop_today_ft_hr     numeric,
  drlg_hrs_today      numeric,
  current_run_ftg     numeric,
  circ_hrs_today      numeric,
  created_at          timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT drilling_core_report_key UNIQUE (report_number, date, well_name),

  -- basic sanity checks
  CONSTRAINT drilling_core_nonnegatives CHECK (
    COALESCE(depth_0000_ft,0)      >= 0 AND
    COALESCE(depth_2400_ft,0)      >= 0 AND
    COALESCE(footage_today_ft,0)   >= 0 AND
    COALESCE(rop_today_ft_hr,0)    >= 0 AND
    COALESCE(drlg_hrs_today,0)     >= 0 AND
    COALESCE(current_run_ftg,0)    >= 0 AND
    COALESCE(circ_hrs_today,0)     >= 0
  )
);

CREATE INDEX IF NOT EXISTS idx_core_date          ON public.drilling_core (date);
CREATE INDEX IF NOT EXISTS idx_core_well          ON public.drilling_core (well_name);
CREATE INDEX IF NOT EXISTS idx_core_report_well   ON public.drilling_core (report_number, well_name);


-- ============================================================
-- Helper macro to reduce repetition (composite FK)
-- (For readability: we’ll inline in each table)
-- ============================================================


-- ============================================================
-- PUMP DATA
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_pump (
  id                      bigserial PRIMARY KEY,
  report_number           text NOT NULL,
  date                    date NOT NULL,
  well_name               text NOT NULL,

  pump_no                 integer,
  bbls_per_stroke         numeric,
  gals_per_stroke         numeric,
  vol_gpm                 numeric,
  spm                     numeric,

  created_at              timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_pump_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE,

  CONSTRAINT pump_nonnegatives CHECK (
    COALESCE(bbls_per_stroke,0) >= 0 AND
    COALESCE(gals_per_stroke,0) >= 0 AND
    COALESCE(vol_gpm,0)         >= 0 AND
    COALESCE(spm,0)             >= 0
  )
);

CREATE INDEX IF NOT EXISTS idx_pump_corekey ON public.drilling_pump (report_number, date, well_name);


-- ============================================================
-- MUD DATA
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_mud (
  id                    bigserial PRIMARY KEY,
  report_number         text NOT NULL,
  date                  date NOT NULL,
  well_name             text NOT NULL,

  weight_ppg            numeric,
  viscosity_sec         numeric,
  pressure_psi          numeric,

  created_at            timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_mud_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE,

  CONSTRAINT mud_nonnegatives CHECK (
    COALESCE(weight_ppg,0)    >= 0 AND
    COALESCE(viscosity_sec,0) >= 0 AND
    COALESCE(pressure_psi,0)  >= 0
  )
);

CREATE INDEX IF NOT EXISTS idx_mud_corekey ON public.drilling_mud (report_number, date, well_name);


-- ============================================================
-- DRILLING PARAMETERS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_params (
  id                          bigserial PRIMARY KEY,
  report_number               text NOT NULL,
  date                        date NOT NULL,
  well_name                   text NOT NULL,

  st_wt_rot_klbs              numeric,
  pu_wt_klbs                  numeric,
  so_wt_klbs                  numeric,
  wob_klbs                    numeric,
  rotary_rpm                  numeric,
  motor_rpm                   numeric,
  total_bit_rpm               numeric,
  rot_tq_off_btm_ftlb         numeric,
  rot_tq_on_btm_ftlb          numeric,
  off_bottom_pressure_psi     numeric,
  on_bottom_pressure_psi      numeric,

  created_at                  timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_params_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_params_corekey ON public.drilling_params (report_number, date, well_name);


-- ============================================================
-- MOTOR DATA
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_motor (
  id                      bigserial PRIMARY KEY,
  report_number           text NOT NULL,
  date                    date NOT NULL,
  well_name               text NOT NULL,

  run_no                  text,
  size_in                 numeric,
  type                    text,
  serial_no               text,
  tool_deflection         numeric,
  avg_diff_press_psi      numeric,
  daily_drill_hrs         numeric,
  daily_circ_hrs          numeric,
  daily_total_hrs         numeric,
  acc_drill_hrs           numeric,
  acc_circ_hrs            numeric,
  depth_in_ft             numeric,
  depth_out_ft            numeric,

  created_at              timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_motor_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_motor_corekey ON public.drilling_motor (report_number, date, well_name);


-- ============================================================
-- BHA
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_bha (
  id              bigserial PRIMARY KEY,
  report_number   text NOT NULL,
  date            date NOT NULL,
  well_name       text NOT NULL,

  item            text,
  od_in           numeric,
  id_in           numeric,
  weight          numeric,
  connection      text,
  length_ft       numeric,
  depth_ft        numeric,

  created_at      timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_bha_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bha_corekey ON public.drilling_bha (report_number, date, well_name);


-- ============================================================
-- SURVEY
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_survey (
  id              bigserial PRIMARY KEY,
  report_number   text NOT NULL,
  date            date NOT NULL,
  well_name       text NOT NULL,

  depth_ft        numeric,
  inc_deg         numeric,
  azi_deg         numeric,

  created_at      timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_survey_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_survey_corekey ON public.drilling_survey (report_number, date, well_name);


-- ============================================================
-- BIT DATA
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_bit (
  id                bigserial PRIMARY KEY,
  report_number     text NOT NULL,
  date              date NOT NULL,
  well_name         text NOT NULL,

  no                integer,
  size_in           numeric,
  mfg               text,
  type              text,
  nozzles_or_tfa    text,
  serial_no         text,
  depth_in_ft       numeric,
  cum_footage_ft    numeric,
  cum_hours         numeric,
  depth_out_ft      numeric,
  dull_ir           text,
  dull_or           text,
  dull_dc           text,
  loc               text,
  bs                text,
  g_16              text,
  oc                text,
  rpld              text,

  created_at        timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_bit_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bit_corekey ON public.drilling_bit (report_number, date, well_name);


-- ============================================================
-- CASING
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_casing (
  id              bigserial PRIMARY KEY,
  report_number   text NOT NULL,
  date            date NOT NULL,
  well_name       text NOT NULL,

  od_in           numeric,
  id_in           numeric,
  weight          numeric,
  grade           text,
  connection      text,
  depth_set_ft    numeric,

  created_at      timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_casing_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_casing_corekey ON public.drilling_casing (report_number, date, well_name);


-- ============================================================
-- DRILL PIPE
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_drillpipe (
  id              bigserial PRIMARY KEY,
  report_number   text NOT NULL,
  date            date NOT NULL,
  well_name       text NOT NULL,

  od_in           numeric,
  id_in           numeric,
  weight          numeric,
  grade           text,
  connection      text,

  created_at      timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_drillpipe_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_drillpipe_corekey ON public.drilling_drillpipe (report_number, date, well_name);


-- ============================================================
-- RENTAL EQUIPMENT
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_rental_equipment (
  id              bigserial PRIMARY KEY,
  report_number   text NOT NULL,
  date            date NOT NULL,
  well_name       text NOT NULL,

  item            text,
  serial_no       text,
  date_received   date,
  date_returned   date,

  created_at      timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_rentaleq_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_rentaleq_corekey ON public.drilling_rental_equipment (report_number, date, well_name);


-- ============================================================
-- TIME BREAKDOWN / FORECAST
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_time_breakdown (
  id                bigserial PRIMARY KEY,
  report_number     text NOT NULL,
  date              date NOT NULL,
  well_name         text NOT NULL,

  from_time         text,
  to_time           text,
  hrs               numeric,
  start_depth_ft    numeric,
  end_depth_ft      numeric,
  cl                text,
  description       text,
  code              text,
  forecast          text,

  created_at        timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_timebk_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE,

  CONSTRAINT time_nonneg CHECK (COALESCE(hrs,0) >= 0)
);

CREATE INDEX IF NOT EXISTS idx_timebk_corekey ON public.drilling_time_breakdown (report_number, date, well_name);


-- ============================================================
-- FUEL
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_fuel (
  id            bigserial PRIMARY KEY,
  report_number text NOT NULL,
  date          date NOT NULL,
  well_name     text NOT NULL,

  fuel_type     text,
  vendor        text,
  begin_qty     numeric,
  received      numeric,
  total         numeric,
  used          numeric,
  remaining     numeric,

  created_at    timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_fuel_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE,

  CONSTRAINT fuel_nonneg CHECK (
    COALESCE(begin_qty,0) >= 0 AND
    COALESCE(received,0)  >= 0 AND
    COALESCE(total,0)     >= 0 AND
    COALESCE(used,0)      >= 0 AND
    COALESCE(remaining,0) >= 0
  )
);

CREATE INDEX IF NOT EXISTS idx_fuel_corekey ON public.drilling_fuel (report_number, date, well_name);


-- ============================================================
-- CHEMICALS
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_chemicals (
  id            bigserial PRIMARY KEY,
  report_number text NOT NULL,
  date          date NOT NULL,
  well_name     text NOT NULL,

  additive      text,
  qty           numeric,
  unit          text,

  created_at    timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_chems_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE,

  CONSTRAINT chems_nonneg CHECK (COALESCE(qty,0) >= 0)
);

CREATE INDEX IF NOT EXISTS idx_chems_corekey ON public.drilling_chemicals (report_number, date, well_name);


-- ============================================================
-- PERSONNEL
-- ============================================================
CREATE TABLE IF NOT EXISTS public.drilling_personnel (
  id            bigserial PRIMARY KEY,
  report_number text NOT NULL,
  date          date NOT NULL,
  well_name     text NOT NULL,

  tour          text,   -- Daylights / Morning / etc.
  role          text,   -- Rig Manager, Driller, Motor Hand, etc.
  name          text,
  hours         numeric,

  created_at    timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT fk_personnel_core
    FOREIGN KEY (report_number, date, well_name)
    REFERENCES public.drilling_core (report_number, date, well_name)
    ON DELETE CASCADE,

  CONSTRAINT personnel_nonneg CHECK (COALESCE(hours,0) >= 0)
);

CREATE INDEX IF NOT EXISTS idx_personnel_corekey ON public.drilling_personnel (report_number, date, well_name);


-- ============================================================
-- OPTIONAL: SIMPLE ROLLUP VIEWS (nice for Metabase)
-- ============================================================

-- Basic “one row per report” rollup joining a few simple aggregates
CREATE OR REPLACE VIEW public.v_drilling_report_summary AS
SELECT
  c.report_number,
  c.date,
  c.well_name,
  c.oil_company,
  c.contractor,
  c.location,
  c.depth_0000_ft,
  c.depth_2400_ft,
  c.footage_today_ft,
  c.rop_today_ft_hr,
  -- examples of simple aggregates
  (SELECT COALESCE(SUM(hrs),0) FROM public.drilling_time_breakdown t
     WHERE t.report_number=c.report_number AND t.date=c.date AND t.well_name=c.well_name)     AS total_hours_logged,
  (SELECT COALESCE(SUM(used),0) FROM public.drilling_fuel f
     WHERE f.report_number=c.report_number AND f.date=c.date AND f.well_name=c.well_name)     AS fuel_used_total,
  (SELECT COALESCE(SUM(qty),0) FROM public.drilling_chemicals ch
     WHERE ch.report_number=c.report_number AND ch.date=c.date AND ch.well_name=c.well_name)  AS chemicals_qty_total
FROM public.drilling_core c;

CREATE INDEX IF NOT EXISTS idx_vsum_date_well ON public.drilling_core (date, well_name);

-- ============================================================
-- RLS (Row Level Security)
-- Leave disabled for now (default in Supabase).
-- If you enable RLS later:
--   1) ALTER TABLE ... ENABLE ROW LEVEL SECURITY;
--   2) Add policies to allow your service role or specific users to insert/select.
-- ============================================================
