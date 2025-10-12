# Customize colors


library(lme4)      # For mixed-effects modeling
library(tidyverse) # For data manipulation
library(lubridate) # For date handling
library(ggplot2)   # For visualization

# Load the cleaned dataset

df  <- read_rds('outputs/data/processed/user_daily_steps_final.rds')
# Convert categorical variables to factors
df <- df %>%
  mutate(
    period = factor(period, levels = c("pre_treatment", "post_treatment")),
    user_id = as.factor(user_id),
    step_count = as.numeric(step_count)  # Ensure step_count is numeric
  ) 


# Fit the Mixed Effects Model
model <- lmer(step_count ~ period + (1 | user_id), data = df)

# View model summary
summary(model)


predic_values  <-  predict(model)
residuals_values  <- residuals(model)

# Checking Assumptions

# 1. Linearity

ggplot(df, aes(x = predict(model), y = step_count)) +
  geom_point(alpha = 0.4) +
  geom_smooth(method = "lm", col = "red") +
  theme_minimal() +
  labs(title = "Observed vs Predicted Step Counts",
       x = "Predicted Step Count",
       y = "Observed Step Count")

# 2. Normality Of Residuals 

# Q-Q Plot for residuals
qqnorm(residuals(model))
qqline(residuals(model), col = "red")

# Histogram of residuals
ggplot(df, aes(x = residuals(model))) +
  geom_histogram(bins = 30, fill = "blue", alpha = 0.5) +
  theme_minimal() +
  labs(title = "Residuals of Mixed Effects Model")

  # Residuals vs Fitted values plot
ggplot(df, aes(x = predic_values, y = residuals_values)) +
  geom_point(alpha = 0.4) +
  geom_smooth(method = "loess", col = "red") +
  labs(title = "Residuals vs Fitted Values",
       x = "Predicted Step Count",
       y = "Residuals")

# Autocorrelation of residuals
acf(residuals_values)



# Can also create a lag plot of residuals
library(ggplot2)
lag_df <- data.frame(
  residual = residuals_values[-length(residuals_values)],
  lag_residual = residuals_values[-1]
)

ggplot(lag_df, aes(x = residual, y = lag_residual)) +
  geom_point(alpha = 0.4) +
  geom_smooth(method = "lm", color = "red") +
  theme_minimal() +
  labs(title = "Lag Plot of Residuals",
       x = "Residual t",
       y = "Residual t+1")

# Q-Q Plot of Random Effects
qqnorm(ranef(model)$user_id[,1])
qqline(ranef(model)$user_id[,1], col = "red")
