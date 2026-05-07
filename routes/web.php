<?php

use App\Http\Controllers\MtDashboardController;
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

Route::get('/mt-dashboard', MtDashboardController::class)
    ->middleware(['auth', 'verified'])
    ->name('mt.dashboard');

Route::get('/awc-dashboard', function () {
    return Inertia::render('TeamRapportage', ['teamCode' => 'AWC']);
})->middleware(['auth', 'verified'])->name('awc.dashboard');

Route::get('/afc-dashboard', function () {
    return Inertia::render('TeamRapportage', ['teamCode' => 'AFC']);
})->middleware(['auth', 'verified'])->name('afc.dashboard');

Route::get('/acc-dashboard', function () {
    return Inertia::render('TeamRapportage', ['teamCode' => 'ACC']);
})->middleware(['auth', 'verified'])->name('acc.dashboard');

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
