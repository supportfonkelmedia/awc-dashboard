<?php

use App\Http\Controllers\KpiDashboardController;
use App\Http\Controllers\KpiDoelInvoerController;
use App\Http\Controllers\KpiFeedbackController;
use App\Http\Controllers\KpiHandmatigInvoerController;
use App\Http\Controllers\KpiPeliqanDataController;
use App\Http\Controllers\KpiScreenDataController;
use App\Http\Controllers\ProfileController;
use Illuminate\Support\Facades\Route;

// Geen landingspagina: gast → login, ingelogd → KPI-dashboard.
Route::get('/', function () {
    return redirect()->route(auth()->check() ? 'dashboard' : 'login');
})->name('home');

// Breeze-home na login/verificatie → KPI-dashboard.
Route::redirect('/dashboard', '/kpi/strategisch')
    ->middleware(['auth', 'verified'])
    ->name('dashboard');

Route::middleware(['auth', 'verified'])
    ->prefix('kpi')
    ->name('kpi.')
    ->group(function () {
        Route::redirect('/', '/kpi/strategisch');
        Route::redirect('/concern', '/kpi/strategisch')->name('concern');

        Route::get('/{scherm}', KpiDashboardController::class)
            ->where('scherm', implode('|', KpiDashboardController::SCREENS))
            ->name('screen');

        Route::get('/peliqan/data', KpiPeliqanDataController::class)->name('peliqan');

        Route::prefix('api')->name('api.')->group(function () {
            Route::get('/screens/{scherm}', [KpiScreenDataController::class, 'screen'])
                ->where('scherm', implode('|', KpiDashboardController::SCREENS))
                ->name('screen');
            Route::get('/drill', [KpiScreenDataController::class, 'drill'])->name('drill');
            Route::get('/controles', [KpiScreenDataController::class, 'controles'])->name('controles');
        });

        Route::post('/invoer/handmatig', [KpiHandmatigInvoerController::class, 'store'])
            ->name('invoer.handmatig');

        Route::post('/invoer/doelen', [KpiDoelInvoerController::class, 'store'])
            ->name('invoer.doelen');

        Route::prefix('feedback')->name('feedback.')->group(function () {
            Route::get('/', [KpiFeedbackController::class, 'index'])->name('index');
            Route::post('/', [KpiFeedbackController::class, 'store'])->name('store');
            Route::patch('/{feedback}', [KpiFeedbackController::class, 'update'])
                ->whereNumber('feedback')
                ->name('update');
            Route::get('/{feedback}/screenshot', [KpiFeedbackController::class, 'screenshot'])
                ->whereNumber('feedback')
                ->name('screenshot');
        });
    });

// Oude URLs (bookmarks) → KPI-schermen.
Route::redirect('/mt-dashboard', '/kpi/strategisch')
    ->middleware(['auth', 'verified'])
    ->name('mt.dashboard');

Route::redirect('/awc-dashboard', '/kpi/awc')
    ->middleware(['auth', 'verified'])
    ->name('awc.dashboard');

Route::redirect('/afc-dashboard', '/kpi/afc')
    ->middleware(['auth', 'verified'])
    ->name('afc.dashboard');

Route::redirect('/acc-dashboard', '/kpi/acc')
    ->middleware(['auth', 'verified'])
    ->name('acc.dashboard');

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');
});

require __DIR__.'/auth.php';
