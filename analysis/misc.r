slider <- function(x, y, window_size = 0.05) {
  out <- rep(NA, length(y))
  upper <- x + (window_size/2)
  lower <- x - (window_size/2)
  for (nn in seq(1, length(y))) {
    out[nn] <- mean(y[x <= upper[nn] & x >= lower[nn]], na.rm = TRUE)
  }
  out
}


dist_from_last <- function(x) {
  res <- rep(NA, length(x))
  for (i in 1:length(x)) {
    if (i == 1) { res[1] <- NA }
    subvec <- x[1:i - 1]
    rev_subvec <- rev(subvec)
    res[i] <- match(x[i], rev_subvec)
  }
  res
}