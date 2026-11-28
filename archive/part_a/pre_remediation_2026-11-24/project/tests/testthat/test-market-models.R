testthat::test_that('OLS recovers known parameters and agrees with independent lm', {
  set.seed(157);x<-rnorm(2000,0,.01);y<-.001+1.2*x+rnorm(2000,0,.0001)
  fit<-fit_market_model(y,x)
  testthat::expect_equal(fit$alpha,.001,tolerance=1e-5)
  testthat::expect_equal(fit$beta,1.2,tolerance=.002)
  testthat::expect_equal(c(fit$alpha,fit$beta),unname(coef(lm(y~x))),tolerance=1e-12)
  testthat::expect_false(fit_market_model(rep(1,20),1:20)$model_ok)
  testthat::expect_false(fit_market_model(1:20,rep(1,20))$model_ok)
})
