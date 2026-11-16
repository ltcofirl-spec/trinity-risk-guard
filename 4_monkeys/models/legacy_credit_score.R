# SC-CREDIT-1.1 | SIMULATED LEGACY R SCORECARD | AUTHOR-GENERATED FOR HACKATHON
# Logistic model and coefficient assumptions are NOT estimated from bank data.
# Reference source for R-to-Python parity; production use is prohibited.
#
# Usage:
#   Rscript models/legacy_credit_score.R synthetic_credit_data.csv outputs/legacy_R_predictions.csv
# Requires only base R.

MODEL_VERSION <- 'SC-CREDIT-1.1'

score_credit <- function(df) {
  required <- c('utilization', 'dti', 'income_k', 'late_payments_12m')
  missing <- setdiff(required, names(df))
  if (length(missing) > 0) stop(paste('Missing required columns:', paste(missing, collapse=', ')))
  if (nrow(df) == 0) stop('Input data must not be empty')
  limits <- list(utilization=c(0,1), dti=c(0,.85), income_k=c(18,180), late_payments_12m=c(0,4))
  for (nm in required) {
    x <- df[[nm]]
    if (!is.numeric(x) || any(!is.finite(x)) || any(x < limits[[nm]][1] | x > limits[[nm]][2])) {
      stop(paste('Invalid numeric range or missing value in', nm))
    }
  }
  if (any(df$late_payments_12m != floor(df$late_payments_12m))) stop('late_payments_12m must be integer')
  if ('customer_id' %in% names(df) && (anyNA(df$customer_id) || anyDuplicated(df$customer_id))) {
    stop('customer_id must be unique and nonmissing')
  }

  # Explanatory odds-ratio assumptions: utilization +10pp -> OR 1.179;
  # DTI +10pp -> OR 1.120; income +EUR10k -> OR 0.960;
  # one late payment -> OR 1.859. Intercept selected to give a
  # reference scenario (U=0.30, DTI=0.32, income_k=50, late=0) PD ~ 8.9%.
  logit <- -2.98 +
           1.65 * df$utilization +
           1.13 * df$dti -
           0.0041 * df$income_k +
           0.62 * df$late_payments_12m
  p <- 1 / (1 + exp(-logit))
  band <- ifelse(p < 0.08, 'LOW', ifelse(p < 0.18, 'MEDIUM', 'HIGH'))
  data.frame(probability=p, risk_band=band, stringsAsFactors=FALSE)
}

args <- commandArgs(trailingOnly=TRUE)
if (length(args) >= 2) {
  input <- read.csv(args[1], stringsAsFactors=FALSE, check.names=FALSE)
  if (!'customer_id' %in% names(input)) stop('customer_id is required for parity audit')
  result <- score_credit(input)
  output <- data.frame(customer_id=input$customer_id,
                       r_probability=result$probability,
                       r_risk_band=result$risk_band,
                       model_version=MODEL_VERSION,
                       stringsAsFactors=FALSE)
  dir.create(dirname(args[2]), recursive=TRUE, showWarnings=FALSE)
  options(digits=17)
  write.csv(output, args[2], row.names=FALSE)
  cat(sprintf('R reference complete: %d rows, version %s\n', nrow(output), MODEL_VERSION))
}
