"""imputations.cs.mice"""
import numpy as np
from sklearn.linear_model import LinearRegression
from impyute.utils import find_null
from impyute.utils import checks

# pylint: disable=too-many-locals
def mice(data):
    """Multivariate Imputation by Chained Equations

    Reference:
        Buuren, S. V., & Groothuis-Oudshoorn, K. (2011). Mice: Multivariate
        Imputation by Chained Equations in R. Journal of Statistical Software,
        45(3). doi:10.18637/jss.v045.i03

    Implementation follows the main idea from the paper above. Differs in
    decision of which variable to regress on (here, I choose it at random).
    Also differs in stopping criterion (here the model stops after change in
    prediction from previous prediction is less than 10%).

    PARAMETERS
    ----------
    data: numpy.ndarray
        Data to impute.

    RETURNS
    -------
    numpy.ndarray
        Imputed data.

    """
    if not checks(data):
        raise Exception("Checks failed")
    null_xy = find_null(data)

    # Add a column of zeros to the index values
    null_xyv = np.append(null_xy, np.zeros((np.shape(null_xy)[0], 1)), axis=1)

    null_xyv = [[int(x), int(y), v] for x, y, v in null_xyv]
    temp = []
    cols_missing = set([y for _, y, _ in null_xyv])

    # Step 1: Simple Imputation, these are just placeholders
    for x_i, y_i, value in null_xyv:
        # Column containing nan value without the nan value
        col = data[:, [y_i]][~np.isnan(data[:, [y_i]])]

        new_value = np.mean(col)
        data[x_i][y_i] = new_value
        temp.append([x_i, y_i, new_value])
    null_xyv = temp

    # Step 5: Repeat step 2 - 4 until convergence (the 100 is arbitrary)

    converged = [False] * len(null_xyv)
    while all(converged):
        # Step 2: Placeholders are set back to missing for one variable/column
        dependent_col = int(np.random.choice(list(cols_missing)))
        missing_xs = [int(x) for x, y, value in null_xyv if y == dependent_col]

        # Step 3: Perform linear regression using the other variables
        x_train, y_train = [], []
        for x_i in (x_i for x_i in range(len(data)) if x_i not in missing_xs):
            x_train.append(np.delete(data[x_i], dependent_col))
            y_train.append(data[x_i][dependent_col])
        model = LinearRegression()
        model.fit(x_train, y_train)

        # Step 4: Missing values for the missing variable/column are replaced
        # with predictions from our new linear regression model
        temp = []
        # For null indices with the dependent column that was randomly chosen
        for i, x_i, y_i, value in enumerate(null_xyv):
            if y_i == dependent_col:
                # Row 'x' without the nan value
                new_value = model.predict(np.delete(data[x_i], dependent_col))
                data[x_i][y_i] = new_value.reshape(1, -1)
                temp.append([x_i, y_i, new_value])
                delta = (new_value-value)/value
                if delta < 0.1:
                    converged[i] = True
        null_xyv = temp
    return data
