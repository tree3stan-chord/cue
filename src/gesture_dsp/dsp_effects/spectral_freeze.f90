module spectral_freeze_mod
  use, intrinsic :: iso_c_binding, only: c_ptr, c_int, c_double
  implicit none

  integer(c_int), parameter :: FFTW_ESTIMATE = 64

  interface
    function fftw_plan_dft_r2c_1d(n, in, out, flags) bind(C, name="fftw_plan_dft_r2c_1d")
      import :: c_int, c_double, c_ptr
      type(c_ptr) :: fftw_plan_dft_r2c_1d
      integer(c_int), value :: n
      real(c_double), dimension(*) :: in
      complex(c_double), dimension(*) :: out
      integer(c_int), value :: flags
    end function fftw_plan_dft_r2c_1d

    subroutine fftw_execute(plan) bind(C, name="fftw_execute")
      import :: c_ptr
      type(c_ptr), value :: plan
    end subroutine fftw_execute

    subroutine fftw_destroy_plan(plan) bind(C, name="fftw_destroy_plan")
      import :: c_ptr
      type(c_ptr), value :: plan
    end subroutine fftw_destroy_plan

    function fftw_plan_dft_c2r_1d(n, in, out, flags) bind(C, name="fftw_plan_dft_c2r_1d")
      import :: c_int, c_double, c_ptr
      type(c_ptr) :: fftw_plan_dft_c2r_1d
      integer(c_int), value :: n
      complex(c_double), dimension(*) :: in
      real(c_double), dimension(*) :: out
      integer(c_int), value :: flags
    end function fftw_plan_dft_c2r_1d
  end interface

contains

  subroutine spectral_freeze(input, output, n) bind(C, name="spectral_freeze")
    implicit none
    integer(c_int), value :: n
    real(c_double), intent(in)  :: input(n)
    real(c_double), intent(out) :: output(n)
    integer :: i, n2
    type(c_ptr) :: plan_fwd, plan_bwd
    complex(c_double), allocatable :: freq(:)

    n2 = n/2 + 1
    allocate(freq(n2))

    ! forward real-to-complex FFT
    plan_fwd = fftw_plan_dft_r2c_1d(n, input, freq, FFTW_ESTIMATE)
    call fftw_execute(plan_fwd)
    call fftw_destroy_plan(plan_fwd)

    ! freeze magnitude (zero phase)
    do i = 1, n2
      freq(i) = cmplx(abs(freq(i)), 0.0d0, kind=c_double)
    end do

    ! inverse complex-to-real FFT
    plan_bwd = fftw_plan_dft_c2r_1d(n, freq, output, FFTW_ESTIMATE)
    call fftw_execute(plan_bwd)
    call fftw_destroy_plan(plan_bwd)

    ! normalize
    do i = 1, n
      output(i) = output(i) / real(n, c_double)
    end do

    deallocate(freq)
  end subroutine spectral_freeze

end module spectral_freeze_mod
