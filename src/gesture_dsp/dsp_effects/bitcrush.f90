module bitcrush_mod
  implicit none
contains

  subroutine bitcrush(input, output, length, bit_depth)
    integer, intent(in) :: length, bit_depth
    real(8), intent(in) :: input(length)
    real(8), intent(out) :: output(length)
    integer :: i
    real(8) :: scale, quantized

    scale = 2.0d0**(bit_depth - 1)
    do i = 1, length
      quantized = nint(input(i) * scale) / scale
      output(i) = quantized
    end do
  end subroutine bitcrush
  
end module bitcrush_mod