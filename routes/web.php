<?php

use App\Http\Controllers\KpiDashboardController;
use App\Http\Controllers\KpiDoelInvoerController;
use App\Http\Controllers\KpiHandmatigInvoerController;
use App\Http\Controllers\KpiPeliqanDataController;
use App\Http\Controllers\KpiScreenDataController;
use App\Http\Controllers\ProfileController;
use Illuminate\Foundation\Application;
use Illuminate\Support\Facades\Route;
use Inertia\Inertia;

Route::get('/', function () {
    return Inertia::render('Welcome', [
        'canLogin' => Route::has('login'),
        'canRegister' => Route::has('register'),
        'laravelVersion' => Application::VERSION,
        'phpVersion' => PHP_VERSION,
    ]);
});

Route::get('/dashboard', function () {
    return Inertia::render('Dashboard');
})->middleware(['auth', 'verified'])->name('dashboard');

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

Route::middleware(['auth', 'verified'])
    ->prefix('operationeel')
    ->name('operationeel.')
    ->group(function () {
        Route::get('/foutenoverzicht', function () {
            return Inertia::render('OperationalModule', ['module' => 'errors']);
        })->name('errors');

        Route::get('/rapportages', function () {
            return Inertia::render('OperationalModule', ['module' => 'reports']);
        })->name('reports');

        Route::get('/communicatie', function () {
            return Inertia::render('OperationalModule', ['module' => 'communication']);
        })->name('communication');

        Route::get('/mijn-teams', function () {
            return Inertia::render('OperationalModule', ['module' => 'teams']);
        })->name('teams');

        Route::get('/tools', function () {
            return Inertia::render('OperationalModule', ['module' => 'tools']);
        })->name('tools');

        Route::get('/gebruikers', function () {
            return Inertia::render('OperationalModule', ['module' => 'users']);
        })->name('users');
    });

Route::middleware('auth')->group(function () {
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
    Route::patch('/profile', [ProfileController::class, 'update'])->name('profile.update');
    Route::delete('/profile', [ProfileController::class, 'destroy'])->name('profile.destroy');
});

require __DIR__.'/auth.php';
