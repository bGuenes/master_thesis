import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
from scipy.stats import norm
from scipy.stats import multivariate_normal

##########################################################################################################
# --- Calculate mean and error ---
def mean_error(x, N_stars):
    mean = np.mean(x)
    std = np.std(x)
    err = std/np.sqrt(N_stars)

    return mean, err, std


##########################################################################################################
# --- Plot 1D Histogram ---

def plot_1d_hist(x1, x2, x_true, names, simulations):
    fig, ax = plt.subplots(1,2, figsize=(12,6))
    plot_width = 0.3
    
    def plot_subplot(i, x, true, name):
        N_stars = int(len(x)/simulations)
        mean, err, std = mean_error(x, N_stars)

        # Set the x-axis limits
        x_min = true - plot_width*true
        x_max = true + plot_width*true

        # Fit a Gaussian to the data
        lin = np.linspace(x_min, x_max, 1000)
        p = norm.pdf(lin, mean, std)

        # Plot the data
        ax[i].hist(x, bins=500, density=True, alpha=0.6, color='g')
        ax[i].plot(lin, p, 'k', linewidth=2)
        ax[i].axvline(x=true, color='r', linestyle='dashed', linewidth=2)
        
        ax[i].set_title(fr"{name}: {true:.3f}"
                        "\n"
                        fr"Fit: {mean:.3f} $\pm$ {err:.3f}")
        ax[i].set_xlim(x_min, x_max)

    for i in [0,1]:
        if i == 0:
            x = x1
        else:
            x = x2

        plot_subplot(i, x, x_true[i], names[i])
    
    fig.suptitle(f'{int(len(x1)/simulations)} Stars', fontsize=30)
    plt.tight_layout()
    plt.show()



##########################################################################################################
# --- 2D Histogram preparation ---
def hist_2d_prep(x1, x2, x_true, N_stars):
    x_lim, y_lim = [-2.8,-1.8],[-3.4,-2.4]

    # --- Fit a 2D Gaussian to the data ---
    mean_1, err_1, std_1 = mean_error(x1, int(N_stars))
    mean_2, err_2, std_2 = mean_error(x2, int(N_stars))

    
    x = np.linspace(x_lim[0], x_lim[1], 1000)
    y = np.linspace(y_lim[0], y_lim[1], 1000)

    X, Y = np.meshgrid(x, y)
    pos = np.empty(X.shape + (2,))

    pos[:, :, 0] = X
    pos[:, :, 1] = Y

    popt, pcov = multivariate_normal.fit(np.array([x1, x2]).T)
    rv = multivariate_normal(popt, pcov)


    # --- Calculate the sigma levels ---
    levels =[]
    sigma = [3,2,1]
    for n in sigma:
        level = rv.pdf(popt+n * np.array([std_1, std_2]))
        levels.append(level)

    return  x_lim, y_lim, X, Y, pos, rv, levels, sigma, mean_1, err_1, std_1, mean_2, err_2, std_2

##########################################################################################################
# --- Plot 2D Histogram ---

def plot_2d_hist(x1, x2, x_true, N_stars):
    x_lim, y_lim, X, Y, pos, rv, levels, sigma, mean_1, err_1, std_1, mean_2, err_2, std_2 = hist_2d_prep(x1, x2, x_true, N_stars)

    # --- Plot the data ---
    plt.figure(figsize=(15,15))
    plt.hist2d(x1, x2, bins=500, range=[x_lim, y_lim])

    # draw contour lines on1,2,3 sigma
    CS = plt.contour(X, Y, rv.pdf(pos), levels=levels, colors='k', linestyles='dashed')
    text = plt.clabel(CS, inline=True, fontsize=10)
    for i in range(len(sigma)):
        text[i].set(text=f'{sigma[i]} $\\sigma$')

    plt.scatter(x_true[0], x_true[1], color='r', label='Ground Truth', s=10)
    plt.errorbar(mean_1, mean_2, yerr=err_2, xerr=err_1, color='k', marker='.')

    plt.title(f'Posterior sampling of {N_stars} stars', fontsize=40)

    plt.xlabel(r'$\alpha_{\rm IMF}$', fontsize=20)
    plt.ylabel(r'$\log_{10} N_{\rm Ia}$', fontsize=20)
    plt.legend()
    plt.show()


##########################################################################################################
# --- Plot 2D Histogram with side plots ---

def plot_2d_hist_sides(x1, x2, x_true, N_stars):
    x_lim, y_lim, X, Y, pos, rv, levels, sigma, mean_1, err_1, std_1, mean_2, err_2, std_2 = hist_2d_prep(x1, x2, x_true, N_stars)

    x = np.linspace(x_lim[0], x_lim[1], 1000)
    y = np.linspace(y_lim[0], y_lim[1], 1000)

    # --- Plot the data ---
    fig = plt.figure(1, figsize=(15,15))
    
    
    # Define the locations for the axes
    left, width = 0.12, 0.7
    bottom, height = 0.12, 0.7
    bottom_h = left_h = left+width+0.02
    
    # Set up the geometry of the three plots
    rect_temperature = [left, bottom, width, height] # dimensions of temp plot
    rect_histx = [left, bottom_h, width, 0.15] # dimensions of x-histogram
    rect_histy = [left_h, bottom, 0.15, height] # dimensions of y-histogram

    # Make the three plots
    axTemperature = plt.axes(rect_temperature) # temperature plot
    axHistx = plt.axes(rect_histx) # x histogram
    axHisty = plt.axes(rect_histy) # y histogram
    
    # Remove the inner axes numbers of the histograms
    nullfmt = NullFormatter()
    axHistx.xaxis.set_major_formatter(nullfmt)
    axHisty.yaxis.set_major_formatter(nullfmt)

    axHistx.axis('off')
    axHisty.axis('off')


    # Plot the data
    axTemperature.hist2d(x1, x2, bins=500, range=[x_lim, y_lim])

    # draw contour lines on sigma levels
    CS = axTemperature.contour(X, Y, rv.pdf(pos), levels=levels, colors='k', linestyles='dashed')
    text = axTemperature.clabel(CS, inline=True, fontsize=10)
    for i in range(len(sigma)):
        text[i].set(text=f'{sigma[i]} $\\sigma$')

    # labels
    label_gt = r'Ground Truth' + f"\n" + r"$\alpha_{\rm IMF} = $" + f'${round(x_true[0].item(), 2)}$' + f"\n" + r"$\log_{10} N_{\rm Ia} = $" + f'${round(x_true[1].item(), 2)}$'
    
    label_fit = r'Fit' + f"\n" + r"$\alpha_{\rm IMF} = $" + f'${round(mean_1.item(), 3)} \\pm {round(err_1.item(),3)}$' + f"\n" + r"$\log_{10} N_{\rm Ia} = $" + f'${round(mean_2.item(), 3)} \\pm {round(err_2.item(),3)}$'
    
    # plot the ground truth and the fit
    legend_true = axTemperature.scatter(x_true[0], x_true[1], color='r', label=label_gt, s=10)
    legend_fit = axTemperature.errorbar(mean_1, mean_2, yerr=err_2, xerr=err_1, color='k', marker='.', label=label_fit)

    axTemperature.set_xlabel(r'$\alpha_{\rm IMF}$', fontsize=20)
    axTemperature.set_ylabel(r'$\log_{10} N_{\rm Ia}$', fontsize=20)
    

    # plot the histograms
    axHistx.hist(x1, bins=500, density=True, alpha=0.6, color='g')
    axHisty.hist(x2, bins=500, density=True, alpha=0.6, color='g', orientation='horizontal')

    axHistx.plot(x, norm.pdf(x, mean_1, std_1), 'k', linewidth=2)
    axHisty.plot(norm.pdf(y, mean_2, std_2), y, 'k', linewidth=2)

    axHistx.axvline(x=x_true[0], color='r', linestyle='dashed', linewidth=2)
    axHisty.axhline(y=x_true[1], color='r', linestyle='dashed', linewidth=2)

    axHistx.set_xlim(x_lim)
    axHisty.set_ylim(y_lim)    

    fig.legend(handles=[legend_true], fontsize=15, shadow=True, fancybox=True, loc=2, bbox_to_anchor=(0.05, 0.92))
    fig.legend(handles=[legend_fit], fontsize=15, shadow=True, fancybox=True, loc=2, bbox_to_anchor=(0.05, 0.99))

    plt.show()


##########################################################################################################
# --- N-Star parameter plot ---

def n_stars_plot(x1, x2, x_true, no_stars= np.array([1, 10, 100, 500, 1000]), simulations=1000):
    fit = []
    err = []

    # --- Fit a 2D Gaussian to the data ---
    for n in no_stars:
        samples = int(n*simulations)
        N_stars = int(samples/simulations)
        mean_1, err_1, _ = mean_error(x1[0:samples], N_stars)
        mean_2, err_2, _ = mean_error(x2[0:samples], N_stars)

        fit.append([mean_1, mean_2])
        err.append([err_1, err_2])
        

    fit = np.array(fit)
    err = np.array(err)

    # --- Plot the data ---
    fig,ax=plt.subplots(nrows=1,ncols=2,figsize=(26,6))

    def plot(fit, err, x_true, ax, name):
        ax.plot(no_stars, fit, color="b", label="Fit")
        ax.fill_between(no_stars, fit-err, fit+err, alpha=0.3,color="b", label=r"1 & 2 $\sigma$")
        ax.fill_between(no_stars, fit-2*err, fit+2*err, alpha=0.2,color="b")

        ax.axhline(x_true, color='k', linestyle=':', linewidth=2, label='Ground Truth')

        ax.set_xlabel(r'$N_{\rm stars}$', fontsize=20)
        ax.set_ylabel(name, fontsize=20)
        ax.set_ylim([x_true-0.2*abs(x_true), x_true+0.2*abs(x_true)])
        ax.set_xscale('log')
        ax.set_xlim([1,1000])

    for i, name in enumerate([r'$\alpha_{\rm IMF}$', r'$\log_{10} N_{\rm Ia}$']):
        plot(fit[:,i], err[:,i], x_true[i], ax[i], name)

    ax[0].legend(fontsize=15, fancybox=True, shadow=True)
    
    plt.tight_layout()
    plt.show()


##########################################################################################################
