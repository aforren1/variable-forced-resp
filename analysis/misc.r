slider <- function(x, y, window_size = 0.05) {
  out <- rep(NA, length(y))
  upper <- x + (window_size/2)
  lower <- x - (window_size/2)
  for (nn in seq(1, length(y))) {
    out[nn] <- mean(y[x <= upper[nn] & x >= lower[nn]], na.rm = TRUE)
  }
  out
}
