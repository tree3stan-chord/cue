module filters_mod
  implicit none
contains


subroutine lp_filter(input, output, n, cutoff, fs)
    !f2py intent(in)  input, n, cutoff, fs
    !f2py intent(out) output
    integer, intent(in) :: n
    real(8), intent(in) :: input(n), cutoff, fs
    real(8), intent(out) :: output(n)
    real(8) :: rc, alpha
    integer :: i

    rc = 1.0d0 / (2.0d0 * 3.141592653589793d0 * cutoff)
    alpha = 1.0d0 / (1.0d0 + rc * fs)
    output(1) = alpha * input(1)
    do i = 2, n
      output(i) = alpha * input(i) + (1.0d0 - alpha) * output(i-1)
    end do
  end subroutine lp_filter

  
  subroutine hp_filter(input, output, n, cutoff, fs)
    !f2py intent(in)  input, n, cutoff, fs
    !f2py intent(out) output
    integer, intent(in) :: n
    real(8), intent(in) :: input(n), cutoff, fs
    real(8), intent(out) :: output(n)
    real(8) :: rc, alpha
    integer :: i

    rc = 1.0d0 / (2.0d0 * 3.141592653589793d0 * cutoff)
    alpha = rc / (rc + 1.0d0 / fs)
    output(1) = input(1)
    do i = 2, n
      output(i) = alpha * (output(i-1) + input(i) - input(i-1))
    end do
  end subroutine hp_filter

end module filters_mod