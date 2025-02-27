"""
Script Name:    Regr_MultipleLinearRegressor

Description:    Defines a numpy algorithm to perform Multiple Linear Regression on a dataset.
"""

from resources.modules.ModelCreationTab import CrossValidationAlgorithms, ModelScoring
import numpy as np
import sys
import statsmodels.api as sm

class Regressor(object):

    NAME = "Gamma GLM Regression"
    WEBSITE = "https://en.wikipedia.org/wiki/Generalized_linear_model"
    DESCRIPTION = "Optimizes a Generalized Linear Model, using a Gamma probability distribution to describe the variance of the data."

    def __init__(self, parent = None, crossValidation = None, scoringParameters = None):

        # Parse arguments
        self.parent = parent
        self.crossValidation = crossValidation if crossValidation != None else "KFOLD_5"
        self.scoringParameters = scoringParameters if scoringParameters != None else ["ADJ_R2"]

        # Data Initializations
        self.x = np.array([[]])     # Raw X Data
        self.y = np.array([])       # Raw Y Data
        self.y_p = np.array([])     # Model Predictions

        # Fitting Parameters
        self.coef = []
        self.intercept = 0

        # Set up cross validator and scorers
        self.scorerClass = self.parent.parent.scorers['class']()
        self.scorers = [getattr(self.scorerClass, scorer) for scorer in self.scoringParameters]
        self.crossValidator = self.parent.parent.crossValidators[self.crossValidation]['module']()
        self.cv_scores = {}
        self.scores = {}
        self.y_p_cv = []

        return


    def regress(self, x, y):
        """
        Performs the Iterative Least Squares fit
        to compute the coefficents of the Gamma
        linear model fit. 
        """

        # Concatenate a row of 1's to the data so that we can compute an intercept
        X_ = np.concatenate((np.ones(shape=x.shape[0]).reshape(-1,1), x), 1)

        # Compute the coefficients and the intercept
        self.model = sm.GLM(y, X_, family=sm.families.Gamma(link=sm.genmod.families.links.log))
        
        self.results = self.model.fit()
        coef = self.results.params[1:]
        intercept = self.results.params[0]

        return coef, intercept


    def fit(self, x, y, crossValidate = False):
        """
        Fits the model with the x and y data, optionally
        cross validates the model and stores cross validation
        scores in the self.cv_scores variable.
        """

        # Set the data references
        self.x = x
        self.y = y

        # Fit the model
        self.coef, self.intercept = self.regress(self.x, self.y)

        # Compute the predicted values
        self.y_p = self.predict(self.x)

        # Compute a score array
        self.scores = self.score()

        # Cross Validate if necessary
        if crossValidate:

            # Create a list to store cross validated predictions
            self.y_p_cv = np.array([], dtype=np.float32)

            # Iterate over the cross validation samples and compute regression scores
            for xsample, ysample, xtest, _ in self.crossValidator.yield_samples(X = self.x, Y = self.y):

                coef, intercept = self.regress(xsample, ysample)
                self.y_p_cv = np.append(self.y_p_cv, self.predict(xtest))
                
            # Compute CV Score
            self.cv_scores = self.score(self.y, self.y_p_cv, self.x.shape[1])
    
        return (self.scores, self.y_p, self.cv_scores, self.y_p_cv) if crossValidate else (self.scores, self.y_p)

    
    def residuals(self):
        """
        Returns the residual time series 
        from the model.
        """
        return self.y - self.y_p


    def predict(self, x):
        """
        Makes a prediction on 'x'
        using the fitted model.
        """
        if len(x.shape) == 1:
            x_ = np.concatenate((np.array([1]), x))
        else:
            x_ = np.concatenate((np.ones(shape=x.shape[0]).reshape(-1,1), x), 1)
        
        return np.array(self.results.predict(x_))
        


    def score(self, y_obs = [], y_p = [], n_features = None):
        """
        Scores the model using the supplied scorers.
        Scores y_obs against y_p. Uses the supplied
        y_p and y_obs (if given), otherwise uses
        the fitted model.
        """

        y_obs = self.y if (y_obs == []) else y_obs
        y_p = self.y_p if (y_p == []) else y_p
        n_features = self.x.shape[1] if (n_features == None) else n_features

        if n_features > len(y_p) - 2:
            return {self.scoringParameters[i]: np.nan for i, scorer in enumerate(self.scorers)}

        return {self.scoringParameters[i]: scorer(y_obs, y_p, n_features) for i, scorer in enumerate(self.scorers)}