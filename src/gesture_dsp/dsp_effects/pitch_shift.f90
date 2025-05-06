module pitch_shift_mod
  implicit none
contains

  subroutine pitch_shift(input, output, n, semitones)
    integer, intent(in) :: n, semitones
    real(8), intent(in) :: input(n)
    real(8), intent(out) :: output(n)
    real(8) :: factor
    integer :: i, idx

    factor = 2.0d0**(semitones/12.0d0)
    do i = 1, n
      idx = int(i / factor)
      if (idx < 1) idx = 1
      if (idx > n) idx = n
      output(i) = input(idx)
    end do
  end subroutine pitch_shift
  
end module pitch_shift_mod